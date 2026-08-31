
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select region
from "weather_analytics"."main"."stg_daily_regional"
where region is null



  
  
      
    ) dbt_internal_test