from typing import BinaryIO
from typing import Callable
from typing import Iterable
from typing import Union

from minio.error import MinioException
from storageprovider.client import StorageProviderClient

ResourceId = Union[int, str]
FileContent = Union[bytes, BinaryIO]


class ContentManager:
    def __init__(
        self,
        temp_container: str,
        storage_provider: StorageProviderClient,
        system_token: Callable[[], str],
    ) -> None:
        self.temp_container = temp_container
        self.storage_provider = storage_provider
        self.system_token = system_token

    def get_object_streaming(
        self, resource_object_id: ResourceId, content_id: ResourceId
    ) -> Iterable[bytes]:
        return self.storage_provider.get_object_streaming(
            str(resource_object_id),
            f"{content_id}".zfill(3),
            system_token=self.system_token(),
        )

    def store_file_content_to_temp_location(self, file_content: FileContent) -> str:
        return self.storage_provider.update_object_and_key(
            self.temp_container, file_content, system_token=self.system_token()
        )

    def copy_temp_content(
        self,
        temporary_storage_key: str,
        target_container_id: ResourceId,
        target_id: ResourceId,
    ) -> None:
        storage_container = str(target_container_id)
        self.storage_provider.copy_object(
            self.temp_container,
            temporary_storage_key,
            storage_container,
            f"{target_id}".zfill(3),
            system_token=self.system_token(),
        )

    def store_content(
        self,
        storage_container_id: ResourceId,
        content_id: ResourceId,
        file_content: FileContent,
    ) -> None:
        self.storage_provider.update_object(
            str(storage_container_id),
            f"{content_id}".zfill(3),
            file_content,
            system_token=self.system_token(),
        )

    def remove_content(
        self, storage_container_id: ResourceId, content_id: ResourceId
    ) -> None:
        self.storage_provider.delete_object(
            str(storage_container_id),
            f"{content_id}".zfill(3),
            system_token=self.system_token(),
        )

    def temp_content_exists(self, object_key: str) -> bool:
        try:
            self.storage_provider.get_object_metadata(
                self.temp_container, object_key, system_token=self.system_token()
            )
            return True
        except MinioException as me:
            if me.code == "NoSuchKey":
                return False
            raise
