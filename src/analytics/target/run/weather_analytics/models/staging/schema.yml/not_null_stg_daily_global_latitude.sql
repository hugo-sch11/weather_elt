
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select latitude
from "weather_analytics"."main"."stg_daily_global"
where latitude is null



  
  
      
    ) dbt_internal_test