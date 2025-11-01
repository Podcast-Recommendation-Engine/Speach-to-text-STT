import grpc
import logging
import json
import time
from vosk import Model, KaldiRecognizer

from src.generated import podcast_transcriber_pb2
from src.generated import podcast_transcriber_pb2_grpc


class PodcastTranscriberServicer(podcast_transcriber_pb2_grpc.PodcastTranscriberServicer):
    def __init__(self, model_path: str, chunk_size: int = 4000):
        self.model_path = model_path
        self.chunk_size = chunk_size
        logging.info(f"Loading Vosk model from: {model_path}")
        try:
            self.model = Model(model_path)
            logging.info("Vosk model loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load Vosk model: {e}")
            raise
    
    def _calculate_confidence(self, words):
        confidences = [w.confidence for w in words if w.confidence > 0]
        return sum(confidences) / len(confidences) if confidences else 0.8
    
    def _extract_words(self, results, enable_word_timestamps):
        """Extract word-level information from Vosk results."""
        words = []
        if not enable_word_timestamps:
            return words
        
        for result in results:
            if 'result' in result:
                for word_info in result['result']:
                    word = podcast_transcriber_pb2.WordInfo(
                        word=word_info.get('word', ''),
                        start_time=word_info.get('start', 0.0),
                        end_time=word_info.get('end', 0.0),
                        confidence=word_info.get('conf', 0.0)
                    )
                    words.append(word)
        return words
    
    def TranscribeStreamingBidirectional(self, request_iterator, context):
        """
        NEW: Bidirectional streaming for unlimited file sizes.
        Client streams audio chunks, server streams back progress.
        NO 2GB LIMIT!
        """
        logging.info("Received TranscribeStreamingBidirectional request")
        start_time = time.time()
        
        try:
            # Storage for received audio
            audio_buffer = bytearray()
            sample_rate = 16000
            channels = 1
            total_size = 0
            filename = "unknown"
            enable_word_timestamps = False
            chunks_received = 0
            
            # Phase 1: Receive audio chunks from client
            logging.info("Starting to receive audio chunks...")
            
            for chunk in request_iterator:
                chunks_received += 1
                
                # First chunk contains metadata
                if chunk.is_first_chunk:
                    sample_rate = chunk.sample_rate if chunk.sample_rate > 0 else 16000
                    channels = chunk.channels if chunk.channels > 0 else 1
                    total_size = chunk.total_size
                    filename = chunk.filename
                    enable_word_timestamps = chunk.enable_word_timestamps
                    
                    logging.info(f"Receiving file: {filename}")
                    logging.info(f"  Sample rate: {sample_rate} Hz")
                    logging.info(f"  Channels: {channels}")
                    logging.info(f"  Total size: {total_size:,} bytes ({total_size / (1024**2):.2f} MB)")
                    logging.info(f"  Enable timestamps: {enable_word_timestamps}")
                    
                    # Send initial progress
                    yield podcast_transcriber_pb2.TranscribeProgressResponse(
                        progress_percentage=0,
                        status=f"Starting upload of {filename}...",
                        partial_transcript=""
                    )
                
                # Append chunk data
                audio_buffer.extend(chunk.audio_data)
                
                # Calculate and report upload progress
                bytes_received = len(audio_buffer)
                upload_progress = min(40, int((bytes_received / total_size) * 40)) if total_size > 0 else 0
                
                # Send progress update every 50 chunks to avoid overwhelming the client
                if chunks_received % 50 == 0:
                    yield podcast_transcriber_pb2.TranscribeProgressResponse(
                        progress_percentage=upload_progress,
                        status=f"Uploading... {bytes_received:,} / {total_size:,} bytes",
                        partial_transcript=""
                    )
                    logging.info(f"Received chunk {chunks_received}, total: {bytes_received:,} bytes")
                
                # Check if this is the last chunk
                if chunk.is_last_chunk:
                    logging.info(f"✅ Received all {chunks_received} chunks ({bytes_received:,} bytes)")
                    yield podcast_transcriber_pb2.TranscribeProgressResponse(
                        progress_percentage=40,
                        status="Upload complete. Starting transcription...",
                        partial_transcript=""
                    )
                    break
            
            # Phase 2: Process audio with Vosk
            audio_bytes = bytes(audio_buffer)
            
            # Skip WAV header if present
            if audio_bytes[:4] == b'RIFF':
                logging.debug("Detected WAV header, skipping 44 bytes")
                audio_bytes = audio_bytes[44:]
            
            logging.info(f"Processing {len(audio_bytes):,} bytes of audio...")
            
            # Create Vosk recognizer
            recognizer = KaldiRecognizer(self.model, sample_rate)
            recognizer.SetWords(enable_word_timestamps)
            
            # Process audio in chunks with progress updates
            total_chunks = (len(audio_bytes) + self.chunk_size - 1) // self.chunk_size
            accumulated_text = []
            full_results = []
            processed_chunks = 0
            
            for chunk_idx in range(0, len(audio_bytes), self.chunk_size):
                chunk_data = audio_bytes[chunk_idx:chunk_idx + self.chunk_size]
                processed_chunks += 1
                
                # Feed chunk to Vosk (maintains context automatically!)
                if recognizer.AcceptWaveform(chunk_data):
                    # Vosk detected a complete sentence/phrase
                    result = json.loads(recognizer.Result())
                    full_results.append(result)
                    
                    if result.get('text'):
                        accumulated_text.append(result['text'])
                
                # Send progress update every 200 chunks
                if processed_chunks % 200 == 0:
                    processing_progress = 40 + int((processed_chunks / total_chunks) * 60)  # 40-100%
                    partial_transcript = " ".join(accumulated_text)
                    
                    yield podcast_transcriber_pb2.TranscribeProgressResponse(
                        progress_percentage=processing_progress,
                        status=f"Transcribing... {processed_chunks}/{total_chunks} chunks",
                        partial_transcript=partial_transcript
                    )
                    logging.info(f"Processed {processed_chunks}/{total_chunks} chunks ({processing_progress}%)")
            
            # Get final result (remaining audio in Vosk's buffer)
            final_result = json.loads(recognizer.FinalResult())
            full_results.append(final_result)
            
            if final_result.get('text'):
                accumulated_text.append(final_result['text'])
            
            # Build final transcript
            transcript = " ".join(accumulated_text)
            
            # Extract word-level information if requested
            words = self._extract_words(full_results, enable_word_timestamps)
            
            # Calculate metrics
            avg_confidence = self._calculate_confidence(words)
            duration = len(audio_bytes) / (sample_rate * channels * 2)  # 2 bytes per sample (16-bit)
            processing_time = time.time() - start_time
            
            # Send final result
            final_response = podcast_transcriber_pb2.TranscribeFileResponse(
                transcript=transcript,
                confidence=avg_confidence,
                duration_seconds=duration,
                processing_time_seconds=processing_time,
                words=words
            )
            
            yield podcast_transcriber_pb2.TranscribeProgressResponse(
                progress_percentage=100,
                partial_transcript=transcript,
                status="Complete!",
                final_result=final_response
            )
            
            logging.info(f"✅ Streaming transcription complete!")
            logging.info(f"   Duration: {duration:.2f}s")
            logging.info(f"   Processing time: {processing_time:.2f}s")
            logging.info(f"   Words: {len(words)}")
            logging.info(f"   Confidence: {avg_confidence:.2%}")
            
        except Exception as e:
            logging.error(f"Error during bidirectional streaming: {e}", exc_info=True)
            yield podcast_transcriber_pb2.TranscribeProgressResponse(
                progress_percentage=0,
                status=f"Error: {str(e)}",
                partial_transcript=""
            )
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Transcription failed: {str(e)}")
