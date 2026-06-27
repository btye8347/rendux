from dataclasses import dataclass
from typing import Any, Protocol


class RegistryError(ValueError):
    pass


class AdapterProtocol(Protocol):
    name: str
    adapter_type: str
    enabled: bool

    def health_check(self) -> "AdapterHealth":
        pass


@dataclass(frozen=True)
class AdapterHealth:
    status: str
    detail: str = ""


@dataclass(frozen=True)
class CapabilityDescriptor:
    name: str
    enabled: bool = True
    description: str = ""


@dataclass(frozen=True)
class AdapterDescriptor:
    name: str
    adapter_type: str
    enabled: bool
    provider: AdapterProtocol


@dataclass(frozen=True)
class CoreRegistries:
    services: "ServiceRegistry"
    capabilities: "CapabilityRegistry"
    adapters: "AdapterRegistry"


class ServiceRegistry:
    def __init__(self) -> None:
        self._services: dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        if name in self._services:
            raise RegistryError(f"Service is already registered: {name}")
        self._services[name] = service

    def get(self, name: str) -> Any:
        return self._services[name]

    def names(self) -> list[str]:
        return list(self._services)


class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: dict[str, CapabilityDescriptor] = {}

    def register(self, capability: CapabilityDescriptor) -> None:
        if capability.name in self._capabilities:
            raise RegistryError(f"Capability is already registered: {capability.name}")
        self._capabilities[capability.name] = capability

    def list(self) -> list[CapabilityDescriptor]:
        return list(self._capabilities.values())


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, AdapterDescriptor] = {}

    def register(self, adapter: AdapterDescriptor) -> None:
        if adapter.name in self._adapters:
            raise RegistryError(f"Adapter is already registered: {adapter.name}")
        self._adapters[adapter.name] = adapter

    def list(self) -> list[AdapterDescriptor]:
        return list(self._adapters.values())

    def health(self) -> dict[str, dict[str, str | bool]]:
        result: dict[str, dict[str, str | bool]] = {}
        for adapter in self._adapters.values():
            health = adapter.provider.health_check()
            result[adapter.name] = {
                "adapter_type": adapter.adapter_type,
                "enabled": adapter.enabled,
                "status": health.status,
                "detail": health.detail,
            }
        return result


def register_core_services() -> CoreRegistries:
    return CoreRegistries(
        services=ServiceRegistry(),
        capabilities=CapabilityRegistry(),
        adapters=AdapterRegistry(),
    )
