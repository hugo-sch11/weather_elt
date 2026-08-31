
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select date
from "weather_analytics"."main"."stg_daily_global"
where date is null



  
  
      
    ) dbt_internal_test