from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

@dataclass
class Journal:
    id: Optional[int] = None
    name: str = ""
    created_at: Optional[datetime] = None

@dataclass
class Author:
    id: Optional[int] = None
    last_name: str = ""
    first_name: Optional[str] = None
    affiliation: Optional[str] = None
    created_at: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        if self.first_name:
            return f"{self.first_name} {self.last_name}"
        return self.last_name
    
@dataclass
class MeshTerm:
    id: Optional[int] = None
    term: str = ""
    created_at: Optional[datetime] = None

@dataclass
class Article:
    id: Optional[int] = None
    pmid: str = ""
    title: str = ""
    abstract: Optional[str] = None
    journal: Optional[Journal] = None
    year: Optional[int] = None
    authors: list[Author] = field(default_factory=list)
    mesh_terms: list[MeshTerm] = field(default_factory=list)
    created_at: Optional[datetime] = None

    authors: list[Author] = field(default_factory=list)
    mesh_terms: list[str] = field(default_factory=list)

    @property
    def journal_name(self) -> Optional[str]:
        if isinstance(self.journal, str):
            return self.journal
        elif self.journal:
            return self.journal.name
        return None

    @property
    def publication_year(self) -> Optional[int]:
        return self.year

    @property
    def author_names(self) -> str:
        return ", ".join(author.full_name for author in self.authors)