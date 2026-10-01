from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DomainStatus = Literal["pending", "verified", "failed", "temporary_failure"]


class DnsRecord(BaseModel):
    record_type: str = Field(alias="recordType")
    name: str
    value: str
    status: Literal["pending", "verified", "failed"]
    ttl: int | None = 300

    model_config = ConfigDict(populate_by_name=True)


class DomainDetail(BaseModel):
    id: str
    name: str
    status: DomainStatus
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
