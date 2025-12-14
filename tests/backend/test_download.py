"""Tests for artifact download endpoints"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json
import tempfile

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), "../../backend")
sys.path.insert(0, backend_path)

from routes.download import (
    extract_hf_repo_id,
    filename_matches_component,
    IteratorFileObj,
    make_presigned_url,
)


class TestExtractHFRepoId:
    """Test HuggingFace repo ID extraction"""
    
    def test_extract_valid_hf_url(self):
        """Test extracting repo ID from valid HF URL"""
        url = "https://huggingface.co/WinKawaks/vit-tiny-patch16-224"
        result = extract_hf_repo_id(url)
        assert result == "WinKawaks/vit-tiny-patch16-224"
    
    def test_extract_hf_url_with_trailing_slash(self):
        """Test extracting repo ID from HF URL with trailing slash"""
        url = "https://huggingface.co/openai/whisper-base/"
        result = extract_hf_repo_id(url)
        assert result == "openai/whisper-base"
    
    def test_extract_single_part_url(self):
        """Test extracting repo ID with only one path component"""
        url = "https://huggingface.co/gpt2"
        result = extract_hf_repo_id(url)
        assert result == "gpt2"
    

class TestFilenameMatchesComponent:
    """Test filename component matching logic"""
    
    def test_match_weights_pytorch_model(self):
        """Test matching pytorch model weights"""
        assert filename_matches_component("pytorch_model.bin", "weights") is True
    
    def test_match_weights_safetensors(self):
        """Test matching safetensors weights"""
        assert filename_matches_component("model.safetensors", "weights") is True
    
    def test_match_weights_pt_file(self):
        """Test matching .pt weight files"""
        assert filename_matches_component("checkpoint.pt", "weights") is True
    
    def test_no_match_weights_config(self):
        """Test config file doesn't match weights"""
        assert filename_matches_component("config.json", "weights") is False
    
    def test_match_tokenizer(self):
        """Test matching tokenizer files"""
        assert filename_matches_component("tokenizer.json", "tokenizer") is True
        assert filename_matches_component("vocab.txt", "tokenizer") is True
        assert filename_matches_component("merges.txt", "tokenizer") is True
    
    def test_no_match_tokenizer(self):
        """Test non-tokenizer file doesn't match"""
        assert filename_matches_component("model.bin", "tokenizer") is False
    
    def test_match_dataset(self):
        """Test matching dataset files"""
        assert filename_matches_component("dataset.parquet", "dataset") is True
        assert filename_matches_component("data/train.csv", "dataset") is True
        assert filename_matches_component("path/data/file.json", "dataset") is True
    
    def test_match_configs(self):
        """Test matching config files"""
        assert filename_matches_component("config.json", "configs") is True
        assert filename_matches_component("model_config.json", "configs") is True
    
    def test_match_full_component(self):
        """Test matching any file with 'full' component"""
        assert filename_matches_component("anything.bin", "full") is True
        assert filename_matches_component("random_file.txt", "full") is True
    
    def test_match_none_component(self):
        """Test matching any file with None component"""
        assert filename_matches_component("anything.bin", None) is True
        assert filename_matches_component("config.json", None) is True


class TestIteratorFileObj:
    """Test IteratorFileObj file adapter"""
    
    def test_readable_returns_true(self):
        """Test readable() method"""
        iterator = iter([b"chunk1", b"chunk2"])
        file_obj = IteratorFileObj(iterator)
        assert file_obj.readable() is True
    
    def test_readinto_basic(self):
        """Test readinto with basic chunks"""
        iterator = iter([b"hello", b"world"])
        file_obj = IteratorFileObj(iterator)
        
        buffer = bytearray(5)
        bytes_read = file_obj.readinto(buffer)
        
        assert bytes_read == 5
        assert bytes(buffer) == b"hello"
    
    def test_readinto_multiple_calls(self):
        """Test multiple readinto calls"""
        iterator = iter([b"abc", b"def", b"ghi"])
        file_obj = IteratorFileObj(iterator)
        
        buffer1 = bytearray(4)
        bytes1 = file_obj.readinto(buffer1)
        assert bytes(buffer1) == b"abcd"
        
        buffer2 = bytearray(3)
        bytes2 = file_obj.readinto(buffer2)
        assert bytes(buffer2) == b"efg"
    
    def test_readinto_eof(self):
        """Test readinto at EOF"""
        iterator = iter([b"data"])
        file_obj = IteratorFileObj(iterator)
        
        buffer1 = bytearray(10)
        file_obj.readinto(buffer1)
        
        buffer2 = bytearray(5)
        bytes_read = file_obj.readinto(buffer2)
        assert bytes_read == 0
    
    def test_read_full(self):
        """Test read() method with -1 to read all"""
        iterator = iter([b"hello", b"world"])
        file_obj = IteratorFileObj(iterator)
        
        data = file_obj.read(-1)
        assert data == b"helloworld"
    
    def test_read_partial(self):
        """Test read() method with size"""
        iterator = iter([b"hello", b"world"])
        file_obj = IteratorFileObj(iterator)
        
        data1 = file_obj.read(3)
        assert data1 == b"hel"
        
        data2 = file_obj.read(4)
        assert data2 == b"lowo"


class TestDownloadModelRoute:
    """Test download_model route"""
    
    def test_download_model_not_found(self, client):
        """Test downloading a model that doesn't exist"""
        response = client.get('/download/nonexistent-model-id')
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_download_model_success(self, client, registry_with_artifact):
        """Test successfully downloading a model"""
        client, sample_artifact = registry_with_artifact
        
        # Add s3_key to the artifact data
        artifact = sample_artifact["test-id-123"]
        artifact["data"]["s3_key"] = "models/test-id-123.zip"
        
        # Update registry
        registry_path = client.application.config['REGISTRY_PATH']
        with open(registry_path, 'w') as f:
            json.dump(sample_artifact, f)
        
        with patch('routes.download.make_presigned_url') as mock_presigned:
            mock_presigned.return_value = "https://s3.example.com/presigned-url"
            response = client.get('/download/test-id-123')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['model_id'] == 'test-id-123'
        assert data['artifact_name'] == 'test-model'
        assert 'url' in data
    
    def test_download_model_no_s3_key(self, client, registry_with_artifact):
        """Test downloading a model without s3_key"""
        client, sample_artifact = registry_with_artifact
        response = client.get('/download/test-id-123')
        assert response.status_code == 500
        data = response.get_json()
        assert 'error' in data


class TestMakePresignedUrl:
    """Test S3 presigned URL generation"""
    
    @patch('routes.download.S3_CLIENT')
    def test_make_presigned_url(self, mock_s3_client):
        """Test generating a presigned URL"""
        mock_s3_client.generate_presigned_url.return_value = "https://s3.example.com/url"
        
        url = make_presigned_url("test-key")
        
        assert url == "https://s3.example.com/url"
        mock_s3_client.generate_presigned_url.assert_called_once()
    
    @patch('routes.download.S3_CLIENT')
    def test_make_presigned_url_custom_expiry(self, mock_s3_client):
        """Test generating presigned URL with custom expiry"""
        mock_s3_client.generate_presigned_url.return_value = "https://s3.example.com/url"
        
        url = make_presigned_url("test-key", expires_in=3600)
        
        # Verify expires_in parameter was passed
        call_args = mock_s3_client.generate_presigned_url.call_args
        assert call_args.kwargs['ExpiresIn'] == 3600
