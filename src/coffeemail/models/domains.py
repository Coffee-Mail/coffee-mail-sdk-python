from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DomainStatus = Literal["pending", "verified", "failed", "temporary_failure"]
DomainStatusReason = Literal["dns_records_missing", "provider_pending", "provider_failed"]
DnsResolution = Literal["found", "absent", "unknown"]


class DnsRecord(BaseModel):
    record_type: str = Field(alias="recordType")
    name: str
    value: str
    status: Literal["pending", "verified", "failed"]
    ttl: int | None = 300

    model_config = ConfigDict(populate_by_name=True)


class SendingIdentity(BaseModel):
    provider: Literal["aws_ses", "none"]
    state: Literal["not_provisioned", "pending", "ready", "failed"]
    last_synced_at: str | None = Field(default=None, alias="lastSyncedAt")

    model_config = ConfigDict(populate_by_name=True)


class DomainDnsCheck(BaseModel):
    ok: bool
    resolution: DnsResolution | None = None
    expected: str | None = None
    got: str | None = None
    matches: list[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class DomainDetail(BaseModel):
    id: str
    name: str
    status: DomainStatus
    status_reason: DomainStatusReason | None = Field(default=None, alias="statusReason")
    sending_identity: SendingIdentity | None = Field(default=None, alias="sendingIdentity")
    checks: dict[str, DomainDnsCheck] | None = None
    spf_record: DnsRecord | None = Field(default=None, alias="spfRecord")
    dkim_records: list[DnsRecord] = Field(default_factory=list, alias="dkimRecords")
    dmarc_record: DnsRecord | None = Field(default=None, alias="dmarcRecord")
    mx_record: DnsRecord | None = Field(default=None, alias="mxRecord")
    created_at: str = Field(alias="createdAt")
    updated_at: str | None = Field(default=None, alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True)


class CreateDomainResponse(BaseModel):
    id: str
    name: str
    status: DomainStatus
    dns_records: list[DnsRecord] = Field(default_factory=list, alias="dnsRecords")
    created_at: str = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True)


class ListDomainsResponse(BaseModel):
    domains: list[DomainDetail] = Field(default_factory=list)
