-- FileMap SQLite 数据库 Schema
-- Version: 0.3.0

-- 文件表
CREATE TABLE IF NOT EXISTS files (
    file_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
    managed BOOLEAN NOT NULL DEFAULT 0,
    mime_type TEXT,
    size INTEGER,
    hash TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    indexed BOOLEAN DEFAULT 0,
    indexed_at TIMESTAMP,
    deleted BOOLEAN DEFAULT 0
);

-- 标签表
CREATE TABLE IF NOT EXISTS tags (
    tag_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category_id TEXT,
    color TEXT,
    description TEXT,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
);

-- 分类表
CREATE TABLE IF NOT EXISTS categories (
    category_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    exclusive BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL
);

-- 文件-标签关联表
CREATE TABLE IF NOT EXISTS file_tags (
    file_id TEXT NOT NULL,
    tag_id TEXT NOT NULL,
    added_at TIMESTAMP NOT NULL,
    PRIMARY KEY (file_id, tag_id),
    FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(tag_id) ON DELETE CASCADE
);

-- 元数据表（用于存储额外的键值对信息）
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP NOT NULL
);

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
CREATE INDEX IF NOT EXISTS idx_files_mime_type ON files(mime_type);
CREATE INDEX IF NOT EXISTS idx_files_created_at ON files(created_at);
CREATE INDEX IF NOT EXISTS idx_files_indexed ON files(indexed);
CREATE INDEX IF NOT EXISTS idx_files_deleted ON files(deleted);

CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);
CREATE INDEX IF NOT EXISTS idx_tags_category ON tags(category_id);

CREATE INDEX IF NOT EXISTS idx_file_tags_file ON file_tags(file_id);
CREATE INDEX IF NOT EXISTS idx_file_tags_tag ON file_tags(tag_id);

-- 初始化元数据
INSERT OR IGNORE INTO metadata (key, value, updated_at) VALUES ('schema_version', '1', CURRENT_TIMESTAMP);
INSERT OR IGNORE INTO metadata (key, value, updated_at) VALUES ('created_at', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
