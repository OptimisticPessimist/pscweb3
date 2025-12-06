"""Azure Blob Storageサービス."""

from azure.storage.blob import BlobServiceClient

from src.config import settings


class BlobStorageService:
    """Azure Blob Storage操作サービス."""

    def __init__(self) -> None:
        """初期化."""
        self.blob_service_client = BlobServiceClient.from_connection_string(
            settings.azure_storage_connection_string
        )
        self.container_name = settings.azure_storage_container_name

    async def upload_file(self, file_content: bytes, blob_name: str) -> str:
        """ファイルをBlob Storageにアップロード.

        Args:
            file_content: ファイル内容
            blob_name: Blob名

        Returns:
            str: Blobパス
        """
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, blob=blob_name
        )
        blob_client.upload_blob(file_content, overwrite=True)
        return blob_name

    async def download_file(self, blob_name: str) -> bytes:
        """Blob Storageからファイルをダウンロード.

        Args:
            blob_name: Blob名

        Returns:
            bytes: ファイル内容
        """
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, blob=blob_name
        )
        download_stream = blob_client.download_blob()
        return download_stream.readall()

    async def delete_file(self, blob_name: str) -> None:
        """Blob Storageからファイルを削除.

        Args:
            blob_name: Blob名
        """
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, blob=blob_name
        )
        blob_client.delete_blob()


blob_storage_service = BlobStorageService()
