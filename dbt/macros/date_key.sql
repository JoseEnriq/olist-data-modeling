{#
    Integer date key in the YYYYMMDD format used by dim_date (e.g. 20170315).
    Returns null when the date is null, so milestones that did not happen
    stay null in the facts.
#}
{% macro date_key(column) -%}
    cast(strftime(cast({{ column }} as date), '%Y%m%d') as integer)
{%- endmacro %}
