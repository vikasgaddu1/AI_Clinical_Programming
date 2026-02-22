/*******************************************************************************
* Macro: %derive_age
* Purpose: Calculate age in years from birth date and reference date
* 
* Parameters:
*   inds     - Input dataset name
*   outds    - Output dataset name
*   brthdt   - Birth date variable (ISO format YYYY-MM-DD, character or numeric SAS date)
*   refdt    - Reference date variable (ISO format YYYY-MM-DD, character or numeric SAS date)
*   agevar   - Output variable name for age (numeric, default: AGE)
*   ageuvar  - Output variable name for age unit (default: AGEU, value='YEARS')
*   create_ageu - Create AGEU variable? (default: Y)
*
* Usage:
*   %derive_age(inds=work.dm, outds=work.dm_age, brthdt=BRTHDTC, refdt=RFSTDTC, agevar=AGE);
*   %derive_age(inds=work.dm, outds=work.dm_age, brthdt=BRTHDTC, refdt=RFSTDTC, agevar=AGE, ageuvar=AGEU, create_ageu=Y);
*
* Notes:
*   - Birth date must be before or equal to reference date
*   - Age is calculated in completed years (using YRDIF function)
*   - Missing dates result in missing age
*   - Output age is numeric
*******************************************************************************/

%macro derive_age(inds=, outds=, brthdt=, refdt=, agevar=AGE, ageuvar=AGEU, create_ageu=Y);

  %if &inds. = %then %do;
    %put ERROR: inds parameter is required;
    %return;
  %end;

  %if &outds. = %then %do;
    %put ERROR: outds parameter is required;
    %return;
  %end;

  %if &brthdt. = %then %do;
    %put ERROR: brthdt parameter is required;
    %return;
  %end;

  %if &refdt. = %then %do;
    %put ERROR: refdt parameter is required;
    %return;
  %end;

  %put NOTE: Deriving age from &brthdt. to &refdt. in &outds.;

  data &outds.;
    set &inds.;
    
    _brthdt_num = .;
    _refdt_num = .;
    
    /* Convert birth date to numeric SAS date if character */
    if vtype(&brthdt.) = 'C' then do;
      /* Assume ISO 8601 format (YYYY-MM-DD) */
      _brthdt_num = input(&brthdt., yymmdd10.);
    end;
    else do;
      /* Already numeric */
      _brthdt_num = &brthdt.;
    end;
    
    /* Convert reference date to numeric SAS date if character */
    if vtype(&refdt.) = 'C' then do;
      /* Assume ISO 8601 format (YYYY-MM-DD) */
      _refdt_num = input(&refdt., yymmdd10.);
    end;
    else do;
      /* Already numeric */
      _refdt_num = &refdt.;
    end;
    
    /* Calculate age in completed years */
    if _brthdt_num ^= . and _refdt_num ^= . then do;
      &agevar. = yrdif(_brthdt_num, _refdt_num, 'ACTUAL');
      
      /* Check if birth date is after reference date (error condition) */
      if _brthdt_num > _refdt_num then do;
        %put WARNING: Birth date after reference date for observation;
        &agevar. = .;
      end;
    end;
    else do;
      &agevar. = .;
    end;
    
    /* Create age unit variable if requested */
    %if %upcase(&create_ageu.) = Y %then %do;
      if &agevar. ^= . then do;
        &ageuvar. = 'YEARS';
      end;
      else do;
        &ageuvar. = '';
      end;
    %end;
    
    /* Drop temporary variables */
    drop _brthdt_num _refdt_num;
  run;

  %put NOTE: Macro %derive_age completed. Age variable created: &agevar.;
  %if %upcase(&create_ageu.) = Y %then %do;
    %put NOTE: Age unit variable created: &ageuvar. = 'YEARS';
  %end;

%mend derive_age;
