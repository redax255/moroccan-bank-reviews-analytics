{{ config(materialized='table') }}

with clean_text as (
    -- Step 1: Clean text first
    select
        bank_name,
        branch_name,
        location,
        review_text,
        -- Apply cleaning: lowercase -> remove non-word/space -> trim -> nullif empty
        nullif(
            trim(
                regexp_replace(
                    lower(review_text), 
                    '[^\w\s]', 
                    '', 
                    'g'
                )
            ), 
            ''
        ) as cleaned_review_text,
        rating,
        review_date,
        scraping_date
    from {{ source('raw_data', 'staging') }}
    where review_text is not null and trim(review_text) != ''
),

filter_and_rate as (
    -- Step 2: Filter out rows where cleaned_review_text is null and standardize rating
    select
        bank_name,
        branch_name,
        location,
        review_text,
        cleaned_review_text,
        case
            when lower(rating) like '%1%' then 1
            when lower(rating) like '%2%' then 2
            when lower(rating) like '%3%' then 3
            when lower(rating) like '%4%' then 4
            when lower(rating) like '%5%' then 5
            else null
        end as rating, -- Standardized rating
        review_date,
        scraping_date
    from clean_text
    where cleaned_review_text is not null -- Filter AFTER cleaning
),

rm_duplicates as (
    -- Step 3: Remove duplicates based on CLEANED text
    select
        bank_name,
        branch_name,
        location,
        review_text,
        cleaned_review_text,
        rating,
        review_date,
        scraping_date
    from (
        select *,
            row_number() over (
                partition by bank_name, branch_name, location, cleaned_review_text, rating
                order by scraping_date desc -- Keep the most recent scraping
            ) as row_num
        from filter_and_rate
    ) as subquery
    where row_num = 1
),

adjust_review_date as (
    -- Step 4: Adjust review_date based on the scraping_date and relative review_date
    select
        bank_name,
        branch_name,
        regexp_replace(location, '^Adresse:\s*', '') as location,
        cleaned_review_text as review_text, -- Use cleaned text
        rating,
        {{ convert_relative_date('review_date', 'scraping_date') }} as review_date,
        scraping_date
    from rm_duplicates
)

-- Final model to create cleaned_reviews table
select
    bank_name,
    concat(
        branch_name, 
        ' ', 
        regexp_replace(location, '^.*?(Avenue|Av\.)', '\1', 'i')
    ) as branch_name,
    location,
    review_text, -- Final cleaned review text
    rating,
    review_date
from adjust_review_date