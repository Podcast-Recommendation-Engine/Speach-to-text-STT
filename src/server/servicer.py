"""PodcastTranscriber service implementation."""
import grpc
import logging
import json
import time
from vosk import Model, KaldiRecognizer

from src.generated import podcast_transcriber_pb2
from src.generated import podcast_transcriber_pb2_grpc


class PodcastTranscriberServicer(podcast_transcriber_pb2_grpc.PodcastTranscriberServicer):
    """Implementation of the PodcastTranscriber gRPC service."""
    
    def __init__(self, model_path: str, chunk_size: int = 4000):
        """
        Initialize the transcriber with a Vosk model.
        
        Args:
            model_path: Path to the Vosk model directory
            chunk_size: Size of audio chunks to process (default: 4000 bytes)
        """
        self.model_path = model_path
        self.chunk_size = chunk_size
        logging.info(f"Loading Vosk model from: {model_path}")
        
        try:
            self.model = Model(model_path)
            logging.info("Vosk model loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load Vosk model: {e}")
            raise
    
    def TranscribeFileStreaming(self, request, context):
        """
        Transcribe audio file with streaming progress updates.
        
        Args:
            request: TranscribeFileRequest containing audio data and options
            context: gRPC context
            
        Yields:
            TranscribeProgressResponse with progress updates
        """
        logging.info("Received TranscribeFileStreaming request")
        start_time = time.time()
        
        try:
            # Validate request
            if not request.audio_data:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("Audio data is required")
                return
            
            # Set defaults
            sample_rate = request.sample_rate if request.sample_rate > 0 else 16000
            channels = request.channels if request.channels > 0 else 1
            
            logging.info(f"Processing audio: {len(request.audio_data)} bytes, "
                        f"{sample_rate}Hz, {channels} channel(s)")
            
            # Create recognizer
            recognizer = KaldiRecognizer(self.model, sample_rate)
            recognizer.SetWords(request.enable_word_timestamps)
            
            # Process audio data
            audio_bytes = request.audio_data
            
            # Skip WAV header if present
            if audio_bytes[:4] == b'RIFF':
                logging.debug("Detected WAV file, skipping header")
                audio_bytes = audio_bytes[44:]
            
            # Process in chunks and stream progress
            total_chunks = (len(audio_bytes) + self.chunk_size - 1) // self.chunk_size
            accumulated_text = []
            full_results = []
            
            for chunk_idx in range(0, len(audio_bytes), self.chunk_size):
                chunk = audio_bytes[chunk_idx:chunk_idx + self.chunk_size]
                
                if recognizer.AcceptWaveform(chunk):
                    result = json.loads(recognizer.Result())
                    full_results.append(result)
                    
                    if result.get('text'):
                        accumulated_text.append(result['text'])
                        
                        # Send progress update
                        progress = int((chunk_idx / len(audio_bytes)) * 100)
                        yield podcast_transcriber_pb2.TranscribeProgressResponse(
                            progress_percentage=progress,
                            partial_transcript=" ".join(accumulated_text),
                            status=f"Processing chunk {chunk_idx // self.chunk_size + 1}/{total_chunks}"
                        )
            
            # Get final result
            final_result = json.loads(recognizer.FinalResult())
            full_results.append(final_result)
            
            if final_result.get('text'):
                accumulated_text.append(final_result['text'])
            
            # Build complete response
            transcript = " ".join(accumulated_text)
            
            # Extract words if requested
            words = self._extract_words(full_results, request.enable_word_timestamps)
            
            # Calculate metrics
            avg_confidence = self._calculate_confidence(words)
            duration = len(audio_bytes) / (sample_rate * channels * 2)
            processing_time = time.time() - start_time
            
            # Send final response
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
                status="Completed",
                final_result=final_response
            )
            
            logging.info(f"Streaming transcription complete: {processing_time:.2f}s")
            
        except Exception as e:
            logging.error(f"Error during streaming transcription: {e}", exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Transcription failed: {str(e)}")
    
    def _extract_words(self, results, enable_timestamps):
        """
        Extract word information from Vosk results.
        
        Args:
            results: List of Vosk recognition results
            enable_timestamps: Whether timestamps are enabled
            
        Returns:
            List of WordInfo messages
        """
        words = []
        if enable_timestamps:
            for result in results:
                if 'result' in result:
                    for word_info in result['result']:
                        words.append(podcast_transcriber_pb2.WordInfo(
                            word=word_info.get('word', ''),
                            start_time=word_info.get('start', 0.0),
                            end_time=word_info.get('end', 0.0),
                            confidence=word_info.get('conf', 0.0)
                        ))
        return words
    
    def _calculate_confidence(self, words):
        """
        Calculate average confidence from word-level confidences.
        
        Args:
            words: List of WordInfo messages
            
        Returns:
            Average confidence score (0.0 to 1.0)
        """
        confidences = [w.confidence for w in words if w.confidence > 0]
        return sum(confidences) / len(confidences) if confidences else 0.8
