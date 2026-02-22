/* ============================================================================ */
/* SAS PROGRAM: Create SAS7BDAT from CSV                                       */
/* Purpose: Convert raw_dm.csv with messy race data to SAS7BDAT format         */
/* Dataset: RAW_DM (raw Demographics domain)                                   */
/* ============================================================================ */

/* Set library references */
LIBNAME RAWDATA "/sessions/affectionate-awesome-johnson/mnt/AI_Clinical_Programming/study_data";

/* Import CSV file */
PROC IMPORT DATAFILE="/sessions/affectionate-awesome-johnson/mnt/AI_Clinical_Programming/study_data/raw_dm.csv"
    OUT=WORK.RAW_DM
    DBMS=CSV
    REPLACE;
    GETNAMES=YES;
    GUESSINGROWS=300;
RUN;

/* Add SAS labels for documentation */
DATA WORK.RAW_DM;
    SET WORK.RAW_DM;
    
    LABEL
        STUDYID = "Study Identifier"
        SITEID = "Site Identifier"
        SUBJID = "Subject Identifier for Study"
        BRTHDT = "Birth Date"
        RFSTDTC = "Reference Start Date/Time"
        SEX = "Sex"
        RACE = "Race (CDISC Standard Terminology)"
        RACEOTH = "Race Other Specify (Free-text)"
        RACEO = "Race Other (Alternative Variable Name)"
        ETHNIC = "Ethnicity"
        AGE = "Age"
        AGEU = "Age Units"
        ARMCD = "Planned Arm Code"
        ARM = "Planned Arm"
        COUNTRY = "Country"
        INVNAM = "Investigator Name";
        
    FORMAT RACE $50.;
    FORMAT RACEOTH $255.;
    FORMAT RACEO $255.;
RUN;

/* Create permanent SAS7BDAT dataset */
PROC DATASETS LIBRARY=RAWDATA NOLIST;
    COPY IN=WORK OUT=RAWDATA;
    SELECT RAW_DM;
QUIT;

/* Verify dataset was created */
PROC CONTENTS DATA=RAWDATA.RAW_DM VARNUM;
    TITLE "SAS7BDAT Dataset Contents";
RUN;

/* Display summary statistics */
PROC PRINT DATA=RAWDATA.RAW_DM (OBS=10);
    TITLE "First 10 observations of RAW_DM";
RUN;

/* Frequency of RACE values */
PROC FREQ DATA=RAWDATA.RAW_DM;
    TABLES RACE / MISSING;
    TITLE "Distribution of RACE Variable";
RUN;

/* Report on RACEOTH populated subjects */
PROC SQL;
    SELECT COUNT(*) AS Total_Obs,
           COUNT(CASE WHEN RACEOTH NOT='' THEN 1 END) AS With_RACEOTH,
           COUNT(CASE WHEN RACEO NOT='' THEN 1 END) AS With_RACEO
    FROM RAWDATA.RAW_DM;
QUIT;

TITLE "RACE/ETHNICITY DATA QUALITY CHECK";
PROC PRINT DATA=RAWDATA.RAW_DM;
    WHERE RACEOTH NOT='';
    VAR SUBJID RACE RACEOTH ETHNIC;
    TITLE2 "Subjects with Race Other Specified";
RUN;

/* End of program */
