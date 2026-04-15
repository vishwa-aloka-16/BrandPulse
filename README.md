# BrandPulse

BrandPulse is an automated ETL pipeline for collecting social media mentions about brands, cleaning the text, analyzing sentiment, and loading the results into a local MySQL database.

The current implementation supports Reddit through public Reddit JSON search endpoints.

## Project Flow

1. Extract Reddit posts for each brand keyword in `config/brands.json`.
2. Clean titles and post bodies into analysis-ready text.
3. Score sentiment with VADER.
4. Upsert mention records into a MySQL table.

## Setup

Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your MySQL credentials. Reddit extraction only needs a descriptive `REDDIT_USER_AGENT`.

## Brand Config

Edit `config/brands.json` to add brands and keywords:

```json
{
  "brands": [
    {
      "name": "Dialog Axiata",
      "keywords": ["Dialog Axiata", "Dialog", "Dialog 4G", "Dialog network"]
    }
  ]
}
```

You can optionally restrict a brand search to specific subreddits:

```json
{
  "name": "Dialog Axiata",
  "keywords": ["Dialog Axiata", "Dialog 4G"],
  "subreddits": ["srilanka", "SriLanka"]
}
```

## Run

Test without writing to MySQL:

```powershell
.\.venv\Scripts\python.exe src\main.py --dry-run
```

Run the full load:

```powershell
.\.venv\Scripts\python.exe src\main.py
```

Useful options:

```powershell
.\.venv\Scripts\python.exe src\main.py --limit 50 --time-filter month --sort new
```

## MySQL Table

The pipeline automatically creates the configured database and `brand_mentions` table if they do not exist, as long as your MySQL user has permission to create databases and tables.

The auto-created table uses this schema:

```sql
create database if not exists brandpulse;
use brandpulse;

create table if not exists brand_mentions (
  id bigint unsigned not null auto_increment primary key,
  brand varchar(255) not null,
  keyword varchar(255) not null,
  source varchar(50) not null,
  source_post_id varchar(100) not null,
  subreddit varchar(255),
  author varchar(255),
  title text,
  body mediumtext,
  text mediumtext not null,
  url text,
  permalink text,
  score int,
  comment_count int,
  created_at datetime,
  sentiment_negative double,
  sentiment_neutral double,
  sentiment_positive double,
  sentiment_compound double,
  sentiment_label varchar(50),
  inserted_at timestamp default current_timestamp,
  updated_at timestamp default current_timestamp on update current_timestamp,
  unique key uq_brand_mentions_source_post (source, source_post_id)
);
```
