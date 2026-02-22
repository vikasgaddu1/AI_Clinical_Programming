/*******************************************************************************
* Macro: %assign_ct
* Purpose: Map raw data values to CDISC Controlled Terminology
*
* Parameters:
*   inds       - Input dataset name
*   outds      - Output dataset name
*   invar      - Input variable with raw values (character or numeric)
*   outvar     - Output variable with CT-mapped values (character)
*   codelist   - CT codelist code (e.g., C66731 for SEX, C74457 for RACE)
*   ctpath     - Path to CT lookup CSV file (default: ./ct_lookup.csv)
*   unmapped   - Action for unmapped values: KEEP, MISSING, or FLAG (default: FLAG)
*   case_insensitive - Compare case-insensitive? (default: Y)
*
* Usage:
*   %assign_ct(inds=work.dm, outds=work.dm_ct, invar=SEX_RAW, outvar=SEX, 
*              codelist=C66731, ctpath=/path/to/ct_lookup.csv);
*   %assign_ct(inds=work.dm, outds=work.dm_ct, invar=RACE_RAW, outvar=RACE, 
*              codelist=C74457, unmapped=MISSING);
*
* Notes:
*   - CT lookup file should be a CSV with columns: CODELIST, RAW_VALUE, CT_VALUE
*   - Output variable is always character
*   - Missing input values result in missing output values
*   - Unmapped values can be kept as-is, set to missing, or flagged in log
*   - Case-insensitive comparison by default (set case_insensitive=N for case-sensitive)
*******************************************************************************/

%macro assign_ct(inds=, outds=, invar=, outvar=, codelist=, ctpath=./ct_lookup.csv, 
                 unmapped=FLAG, case_insensitive=Y);

  %if &inds. = %then %do;
    %put ERROR: inds parameter is required;
    %return;
  %end;

  %if &outds. = %then %do;
    %put ERROR: outds parameter is required;
    %return;
  %end;

  %if &invar. = %then %do;
    %put ERROR: invar parameter is required;
    %return;
  %end;

  %if &outvar. = %then %do;
    %put ERROR: outvar parameter is required;
    %return;
  %end;

  %if &codelist. = %then %do;
    %put ERROR: codelist parameter is required;
    %return;
  %end;

  %put NOTE: Assigning CT values for codelist &codelist. using &ctpath.;

  /* Check if CT lookup file exists */
  %if not %sysfunc(fileexist(&ctpath.)) %then %do;
    %put ERROR: CT lookup file does not exist: &ctpath.;
    %return;
  %end;

  /* Import CT lookup file */
  proc import datafile="&ctpath." out=_ct_lookup dbms=csv replace;
    getnames=yes;
  run;

  /* Filter to requested codelist */
  data _ct_lookup_subset;
    set _ct_lookup(where=(CODELIST = "&codelist."));
  run;

  /* Check if codelist exists in lookup file */
  %let _nobs=0;
  data _null_;
    if 0 then set _ct_lookup_subset nobs=_nobs;
    call symputx('_nobs', _nobs);
    stop;
  run;

  %if &_nobs. = 0 %then %do;
    %put WARNING: Codelist &codelist. not found in CT lookup file. All values will be treated as unmapped.;
  %end;

  /* Merge with CT lookup and assign values */
  proc sql noprint;
    create table &outds. as
    select
      a.*,
      case
        %if %upcase(&case_insensitive.) = Y %then %do;
          when upcase(b.raw_value) = upcase(a.&invar.) then b.ct_value
        %end;
        %else %do;
          when b.raw_value = a.&invar. then b.ct_value
        %end;
        else ''
      end as &outvar._temp
    from &inds. a
    left join _ct_lookup_subset b
      on 
      %if %upcase(&case_insensitive.) = Y %then %do;
        upcase(a.&invar.) = upcase(b.raw_value)
      %end;
      %else %do;
        a.&invar. = b.raw_value
      %end;
    ;
  quit;

  /* Process based on unmapped action */
  data &outds.;
    set &outds.;
    
    _input_val = strip(&invar.);
    
    /* Initialize output variable */
    if _input_val = '' then do;
      &outvar. = '';
    end;
    else if &outvar._temp ^= '' then do;
      &outvar. = &outvar._temp;
    end;
    else do;
      /* Unmapped value */
      %if %upcase(&unmapped.) = KEEP %then %do;
        &outvar. = _input_val;
        %put WARNING: Unmapped value in codelist &codelist.: "&_input_val.";
      %end;
      %else %if %upcase(&unmapped.) = MISSING %then %do;
        &outvar. = '';
        %put WARNING: Setting unmapped value to missing in codelist &codelist.: "&_input_val.";
      %end;
      %else %do;
        &outvar. = _input_val;
        %put WARNING: Unmapped value in codelist &codelist.: "&_input_val.";
      %end;
    end;
    
    drop &outvar._temp _input_val;
  run;

  /* Clean up temporary datasets */
  proc delete data=_ct_lookup _ct_lookup_subset;
  run;
  quit;

  %put NOTE: Macro %assign_ct completed. Output dataset: &outds. Variable: &outvar.;

%mend assign_ct;
