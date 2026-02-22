/*******************************************************************************
* Macro: %iso_date
* Purpose: Convert non-standard date values to ISO 8601 format (YYYY-MM-DD)
* 
* Parameters:
*   inds     - Input dataset name
*   outds    - Output dataset name
*   invar    - Input variable containing the date string
*   outvar   - Output variable name for the ISO date (character)
*   infmt    - (Optional) Specific input format. If blank, auto-detects:
*              DD-MON-YYYY, MM/DD/YYYY, DD/MM/YYYY, DDMONYYYY
*
* Usage:
*   %iso_date(inds=raw.dm, outds=work.dm_iso, invar=BRTHDT, outvar=BRTHDTC);
*   %iso_date(inds=raw.dm, outds=work.dm_iso, invar=RFSTDTC, outvar=RFSTDTC, infmt=DDMMYYYY10.);
*
* Notes:
*   - Output is always character in YYYY-MM-DD format per SDTM requirements
*   - Missing input values result in missing output values
*   - Invalid dates are set to missing and logged to the SAS log
*   - The macro handles leading/trailing spaces automatically
*******************************************************************************/

%macro iso_date(inds=, outds=, invar=, outvar=, infmt=);

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

  %put NOTE: Converting &invar. to ISO 8601 format in &outds.;

  data &outds.;
    set &inds.;
    
    /* Get the input value and trim spaces */
    _input_val = strip(&invar.);
    _date_num = .;
    
    /* Initialize output variable */
    &outvar. = '';
    
    /* If input is missing, output is missing */
    if _input_val = '' then do;
      &outvar. = '';
    end;
    else do;
      /* Auto-detect format if infmt not specified */
      %if &infmt. = %then %do;
        /* Try DD-MON-YYYY (e.g., 01-JAN-2020) */
        if prxmatch('/^\d{1,2}-[A-Z]{3}-\d{4}$/', upcase(_input_val)) then do;
          _date_num = input(_input_val, DDMONYY10.);
          if _date_num = . then _date_num = input(_input_val, DDMONYYY10.);
        end;
        
        /* Try DD/MM/YYYY (e.g., 01/12/2020) - check if first part > 12 */
        else if prxmatch('/^\d{1,2}\/\d{1,2}\/\d{4}$/', _input_val) then do;
          _parts = scan(_input_val, 1, '/');
          if input(_parts, best.) > 12 then do;
            _date_num = input(_input_val, DDMMYY10.);
            if _date_num = . then _date_num = input(_input_val, DDMMYYYY10.);
          end;
          else do;
            /* Assume MM/DD/YYYY */
            _date_num = input(_input_val, MMDDYY10.);
            if _date_num = . then _date_num = input(_input_val, MMDDYYYY10.);
          end;
        end;
        
        /* Try MM/DD/YYYY (e.g., 12/01/2020) */
        else if prxmatch('/^\d{1,2}\/\d{1,2}\/\d{4}$/', _input_val) then do;
          _date_num = input(_input_val, MMDDYY10.);
          if _date_num = . then _date_num = input(_input_val, MMDDYYYY10.);
        end;
        
        /* Try DDMONYYYY (e.g., 01JAN2020) */
        else if prxmatch('/^\d{2}[A-Z]{3}\d{4}$/', upcase(_input_val)) then do;
          _date_num = input(_input_val, DDMONYY8.);
          if _date_num = . then _date_num = input(_input_val, DDMONYYY8.);
        end;
        
        /* Try YYYY-MM-DD (already ISO format) */
        else if prxmatch('/^\d{4}-\d{2}-\d{2}$/', _input_val) then do;
          _date_num = input(_input_val, YYMMDD10.);
        end;
      %end;
      %else %do;
        /* Use specified format */
        _date_num = input(_input_val, &infmt.);
      %end;
      
      /* Convert numeric date to ISO 8601 character format */
      if _date_num ^= . then do;
        &outvar. = put(_date_num, YYMMDD10.);
      end;
      else do;
        %put WARNING: Could not parse date value "&_input_val." for observation from &invar.;
        &outvar. = '';
      end;
    end;
    
    /* Drop temporary variables */
    drop _input_val _date_num _parts;
  run;

  %put NOTE: Macro %iso_date completed. Output dataset: &outds.;

%mend iso_date;
