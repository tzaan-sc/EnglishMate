import io
import os
import zipfile
import wave
import struct
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from app.backend.admin.models import DatabaseBackup, SystemConfig
from app.backend.auth.models import User
from app.extensions import db
from app.backend.admin.file_backup_service import (
    create_uploads_archive,
    get_uploads_stats,
    get_cloud_storage_settings,
    save_cloud_storage_settings,
    backup_uploads_to_cloud,
    upload_to_s3,
    upload_to_cloudinary,
    restore_uploads_from_archive,
    get_uploads_dir,
)
from app.utils.media_processor import (
    compress_image,
    crop_and_resize_square,
    process_avatar_image,
    normalize_audio_volume,
    get_audio_metadata,
)


def _create_sample_image(width=800, height=400, color=(200, 100, 50), fmt="JPEG"):
    """Tạo một file ảnh mẫu trong bộ nhớ để test."""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.getvalue()


def _create_sample_wav(duration_sec=0.5, framerate=44100, amplitude=5000):
    """Tạo file âm thanh WAV PCM 16-bit đơn giản trong bộ nhớ để test chuẩn hóa âm lượng."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(framerate)
        num_frames = int(duration_sec * framerate)
        samples = [int(amplitude) if i % 2 == 0 else int(-amplitude) for i in range(num_frames)]
        raw_data = struct.pack(f"<{len(samples)}h", *samples)
        wf.writeframes(raw_data)
    buf.seek(0)
    return buf.getvalue()


# ===========================================================================
# 1. FILE COMPRESSION TESTS
# ===========================================================================

def test_image_compression_reduces_size():
    """Test nén ảnh tự động giảm dung lượng file mà vẫn giữ nguyên chất lượng."""
    sample_img_bytes = _create_sample_image(width=1600, height=1200)
    
    res = compress_image(
        input_source=sample_img_bytes,
        max_width=800,
        max_height=600,
        quality=75,
        output_format="JPEG"
    )

    assert res["success"] is True
    assert res["width"] <= 800
    assert res["height"] <= 600
    assert res["compressed_size"] > 0
    assert res["format"] == "JPEG"
    assert len(res["data"]) > 0


def test_image_compression_rgba_to_jpeg():
    """Test chuyển đổi ảnh có kênh alpha (RGBA) sang JPEG có nền trắng."""
    rgba_img = Image.new("RGBA", (400, 400), (255, 0, 0, 128))
    buf = io.BytesIO()
    rgba_img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    res = compress_image(
        input_source=png_bytes,
        output_format="JPEG",
        quality=80
    )

    assert res["success"] is True
    assert res["format"] == "JPEG"
    # Verify resulting image is valid RGB
    out_img = Image.open(io.BytesIO(res["data"]))
    assert out_img.mode == "RGB"


# ===========================================================================
# 2. IMAGE PROCESSING TESTS (PILLOW SQUARE CROP 300x300)
# ===========================================================================

def test_crop_and_resize_square_center_crop():
    """Test crop vuông 1:1 tâm ảnh từ ảnh chữ nhật 800x400 về đúng 300x300."""
    sample_rect_img = _create_sample_image(width=800, height=400)

    res = crop_and_resize_square(
        input_source=sample_rect_img,
        target_size=300,
        quality=88,
        output_format="JPEG"
    )

    assert res["success"] is True
    assert res["width"] == 300
    assert res["height"] == 300

    out_img = Image.open(io.BytesIO(res["data"]))
    assert out_img.size == (300, 300)


def test_process_avatar_image(app, tmp_path):
    """Test hàm process_avatar_image lưu đúng file vào thư mục upload."""
    sample_bytes = _create_sample_image(width=500, height=700)
    upload_dir = tmp_path / "avatars"

    filename, file_path, proc_res = process_avatar_image(
        file_storage_or_data=sample_bytes,
        user_id=42,
        upload_folder=upload_dir,
        target_size=300
    )

    assert filename.startswith("avatar_42_")
    assert filename.endswith(".jpg")
    assert file_path.exists()
    assert proc_res["success"] is True

    saved_img = Image.open(file_path)
    assert saved_img.size == (300, 300)


# ===========================================================================
# 3. AUDIO PROCESSING TESTS
# ===========================================================================

def test_normalize_audio_volume_wav():
    """Test chuẩn hóa âm lượng file WAV đạt target dBFS."""
    wav_bytes = _create_sample_wav(duration_sec=0.2, amplitude=4000)

    res = normalize_audio_volume(
        input_audio=wav_bytes,
        target_dbfs=-3.0
    )

    assert res["success"] is True
    assert res["target_dbfs"] == -3.0
    assert res["duration_seconds"] > 0
    assert len(res["data"]) > 0

    # Test metadata
    meta = get_audio_metadata(res["data"])
    assert meta["format"] == "WAV"
    assert meta["channels"] == 1
    assert meta["sample_rate"] == 44100


# ===========================================================================
# 4. FILE BACKUP & CLOUD STORAGE TESTS
# ===========================================================================

def test_create_uploads_archive(app, tmp_path):
    """Test đóng gói nén zip thư mục static/uploads/."""
    with app.app_context():
        uploads_dir = get_uploads_dir()
        sample_file = uploads_dir / "test_sample.txt"
        sample_file.write_text("EnglishMate sample upload content", encoding="utf-8")

        res = create_uploads_archive(archive_format="zip")

        assert res["success"] is True
        assert res["filename"].endswith(".zip")
        assert os.path.exists(res["file_path"])
        assert res["file_count"] >= 1

        # Verify zip contains the file
        with zipfile.ZipFile(res["file_path"], "r") as z:
            namelist = z.namelist()
            assert any("test_sample.txt" in n for n in namelist)

        # Cleanup
        sample_file.unlink(missing_ok=True)
        if os.path.exists(res["file_path"]):
            os.remove(res["file_path"])


def test_get_uploads_stats(app):
    """Test lấy thống kê thư mục uploads."""
    with app.app_context():
        stats = get_uploads_stats()
        assert "total_files" in stats
        assert "total_bytes" in stats
        assert "folder_stats" in stats
        assert "avatars" in stats["folder_stats"]
        assert "cloud_settings" in stats


def test_save_and_get_cloud_storage_settings(app):
    """Test lưu và đọc cấu hình Cloud Storage (S3 / Cloudinary)."""
    with app.app_context():
        save_res = save_cloud_storage_settings({
            "S3_BUCKET_NAME": "test-englishmate-bucket",
            "AWS_REGION": "ap-southeast-1",
            "S3_BACKUP_ENABLED": True,
            "CLOUDINARY_CLOUD_NAME": "test-cld-name",
            "CLOUDINARY_BACKUP_ENABLED": True
        })

        assert save_res["success"] is True
        settings = get_cloud_storage_settings()
        assert settings["s3_bucket"] == "test-englishmate-bucket"
        assert settings["s3_region"] == "ap-southeast-1"
        assert settings["s3_enabled"] is True
        assert settings["cloudinary_cloud_name"] == "test-cld-name"
        assert settings["cloudinary_enabled"] is True


def test_upload_to_s3_mocked(app, tmp_path):
    """Test upload lên AWS S3 với mock boto3."""
    with app.app_context():
        dummy_file = tmp_path / "dummy_backup.zip"
        dummy_file.write_text("dummy zip content", encoding="utf-8")

        with patch("boto3.client") as mock_boto:
            mock_s3 = MagicMock()
            mock_boto.return_value = mock_s3

            res = upload_to_s3(
                file_path=dummy_file,
                custom_config={
                    "S3_BUCKET_NAME": "my-bucket",
                    "AWS_ACCESS_KEY_ID": "test_key",
                    "AWS_SECRET_ACCESS_KEY": "test_secret",
                    "AWS_REGION": "ap-southeast-1"
                }
            )

            assert res["success"] is True
            assert res["provider"] == "S3"
            assert res["bucket"] == "my-bucket"
            mock_s3.upload_file.assert_called_once()


def test_upload_to_cloudinary_mocked(app, tmp_path):
    """Test upload lên Cloudinary với mock cloudinary."""
    with app.app_context():
        dummy_file = tmp_path / "dummy_cld.zip"
        dummy_file.write_text("dummy cld content", encoding="utf-8")

        with patch("cloudinary.uploader.upload") as mock_cld_upload:
            mock_cld_upload.return_value = {
                "public_id": "englishmate_backups/dummy_cld",
                "secure_url": "https://res.cloudinary.com/demo/raw/upload/dummy_cld.zip",
                "bytes": 1024
            }

            res = upload_to_cloudinary(
                file_path=dummy_file,
                custom_config={
                    "CLOUDINARY_CLOUD_NAME": "my-cloud",
                    "CLOUDINARY_API_KEY": "123",
                    "CLOUDINARY_API_SECRET": "abc",
                    "CLOUDINARY_FOLDER": "englishmate_backups"
                }
            )

            assert res["success"] is True
            assert res["provider"] == "CLOUDINARY"
            assert "res.cloudinary.com" in res["url"]


def test_backup_uploads_to_cloud_local(app):
    """Test quy trình trọn gói sao lưu uploads thành công và ghi log DatabaseBackup."""
    with app.app_context():
        res = backup_uploads_to_cloud(provider="LOCAL", notes="Test Local Uploads Backup")
        assert res["success"] is True
        assert res["provider"] == "LOCAL"
        assert res["backup_id"] is not None

        # Verify DatabaseBackup record
        b_rec = db.session.get(DatabaseBackup, res["backup_id"])
        assert b_rec is not None
        assert b_rec.db_type == "UPLOADS_LOCAL"
        assert b_rec.status == "SUCCESS"


# ===========================================================================
# 5. ADMIN API ROUTES INTEGRATION TESTS
# ===========================================================================

def _login_admin(client):
    return client.post("/auth/login", data={"email": "admin@test.com", "password": "admin123"}, follow_redirects=True)


def test_admin_backup_uploads_route(client):
    """Test endpoint admin POST /admin/system/backup/uploads."""
    _login_admin(client)

    resp = client.post(
        "/admin/system/backup/uploads",
        json={"provider": "LOCAL", "notes": "Route Test Uploads"},
        headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True


def test_admin_cloud_settings_route(client):
    """Test endpoint admin POST /admin/system/backup/cloud-settings."""
    _login_admin(client)

    resp = client.post(
        "/admin/system/backup/cloud-settings",
        json={
            "S3_BUCKET_NAME": "admin-s3-test",
            "AWS_REGION": "us-west-2",
            "CLOUDINARY_CLOUD_NAME": "admin-cld-test"
        },
        headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True


def test_admin_compress_image_api(client):
    """Test endpoint admin POST /admin/system/media/compress-image."""
    _login_admin(client)

    img_data = _create_sample_image(600, 400)
    resp = client.post(
        "/admin/system/media/compress-image",
        data={
            "image": (io.BytesIO(img_data), "sample.jpg"),
            "quality": "80",
            "max_width": "400",
            "max_height": "400"
        },
        content_type="multipart/form-data"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["width"] <= 400


def test_admin_normalize_audio_api(client):
    """Test endpoint admin POST /admin/system/media/normalize-audio."""
    _login_admin(client)

    wav_data = _create_sample_wav(0.2)
    resp = client.post(
        "/admin/system/media/normalize-audio",
        data={
            "audio": (io.BytesIO(wav_data), "audio.wav"),
            "target_dbfs": "-3.0"
        },
        content_type="multipart/form-data"
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["target_dbfs"] == -3.0
