
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select longitude
from "weather_analytics"."main"."stg_daily_global"
where longitude is null



  
  
      
    ) dbt_internal_test