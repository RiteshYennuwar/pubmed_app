DROP TABLE IF EXISTS article_meah CASCADE;
DROP TABLE IF EXISTS article_authors CASCADE;
DROP TABLE IF EXISTS articles CASCADE;
DROP TABLE IF EXISTS authors CASCADE;
DROP TABLE IF EXISTS journals CASCADE;
DROP TABLE IF EXISTS mesh_terms CASCADE;


CREATE TABLE journals (
    id SERIAL PRIMARY KEY,
    name VARCHAR(512) UNIQUE NOT NULL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_journal_name ON journals(name);

CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    last_name VARCHAR(256) NOT NULL,
    first_name VARCHAR(256),
    affiliation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (last_name, first_name)
);

CREATE INDEX idx_author_last_name ON authors(last_name);
CREATE INDEX idx_author_name ON authors(last_name, first_name);

CREATE TABLE mesh_terms (
    id SERIAL PRIMARY KEY,
    term VARCHAR(512) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mesh_term ON mesh_terms(term);

CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    pmid VARCHAR(32) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    journal_id INTEGER REFERENCES journals(id) ON DELETE SET NULL,
    publication_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_article_pmid ON articles(pmid);
CREATE INDEX idx_article_publication_year ON articles(publication_year);
CREATE INDEX idx_article_journal_id ON articles(journal_id);
CREATE INDEX idx_article_title ON articles USING gin(to_tsvector('english', title));
CREATE INDEX idx_article_abstract ON articles USING gin(to_tsvector('english', abstract));

CREATE TABLE article_authors (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    author_id INTEGER REFERENCES authors(id) ON DELETE CASCADE,
    author_postion INTEGER NOT NULL,

    UNIQUE (article_id, author_id)

    CONSTRAINT valid_position CHECK (author_postion >= 1)
);

CREATE INDEX idx_article_authors_article_id ON article_authors(article_id);
CREATE INDEX idx_article_authors_author_id ON article_authors(author_id);

CREATE TABLE article_meah (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    mesh_term_id INTEGER REFERENCES mesh_terms(id) ON DELETE CASCADE,

    UNIQUE (article_id, mesh_term_id)
);

CREATE INDEX idx_article_meah_article_id ON article_meah(article_id);
CREATE INDEX idx_article_meah_mesh_term_id ON article_meah(mesh_term_id);

CREATE OR REPLACE VIEW v_articles_full AS
SELECT
    a.id AS article_id,
    a.pmid,
    a.title,
    a.abstract,
    j.name AS journal_name,
    a.publication_year,
    a.created_at,
FROM articels a
LEFT JOIN journals j ON a.journal_id = j.id;


CREATE OR REPLACE VIEW v_articels_summmary AS
SELECT
    a.id AS article_id,
    a.pmid,
    a.title,
    j.name AS journal_name,
    a.publication_year,
    COUNT(DISTINCT aa.author_id) AS author_count,
    COUNT(DISTINCT am.mesh_term_id) AS mesh_term_count,
FROM articels a
LEFT JOIN journals j ON a.journal_id = j.id
LEFT JOIN article_authors aa ON a.id = aa.article_id
LEFT JOIN article_meah am ON a.id = am.article_id
GROUP BY a.id,a.pmid,a.title,a.publication_year,j.name;

CREATE OR REPLACE FUNCTION get_article_authors(p_article_id INTEGER)
RETURNS TEXT AS $$
    SELECT STRING_AGG(
        CONCAT(a.last_name, ' ', COALESCE(a.first_name, '')),
        ', ' 
        ORDER BY aa.author_postion
    )
    FROM article_authors aa
    JOIN authors a ON aa.author_id = a.id
    WHERE aa.article_id = p_article_id;
$$ LANGUAGE SQL;

CREATE OR REPLACE FUNCTION get_article_mesh_terms(p_article_id INTEGER)
RETURNS TEXT[] AS $$
    SELECT STRING_AGG(m.descriptor ORDER BY m.descriptor)
    FROM article_meah am
    JOIN mesh_terms m ON am.mesh_term_id = m.id
    WHERE am.article_id = p_article_id;
$$ LANGUAGE SQL;