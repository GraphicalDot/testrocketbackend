# This file contains the alter table statements applied on the db. The format of each change is like below
```
<last git commit hash>
```
```
<alter sql statement/s>
```
 
# Alter statements

0803422da42aa8e3298d1ba77eed6f03151b8818
alter table mock_tests add column syllabus text;
alter table questions add column is_similarity_marked boolean default false;
alter table attempted_mock_tests add column pdf_report_url text;
alter table batches drop constraint batches_name_key;
alter table batches add constraint batches_name_institute_id_key unique(name, institute_id);
alter table batches add column status integer;
alter table attempted_mock_tests alter column score type decimal;
alter table students add column school varchar(100);
alter table students add column ntse_score decimal;
alter table students add column roll_no varchar(20);
alter table students add column pin varchar(10);
alter table students add column father_email varchar(200);

a646fbcd49aaf9d8c2dbe51e0d905d4ed07153f8
alter table students add column fp_token varchar(64);
alter table institutes add column fp_token varchar(64);

a1589ec1c511640ad68b65cf6e2f782fbd6da384
alter table mock_tests add column cutoff decimal;

ce8b99f0054f5c5f3bf4cc54acfe75e4e631706a
alter table students add column refcode varchar(200);

4fb65a48d28fe7447e528659f9759a47ce3320a2
ALTER TYPE batch_types_enum ADD VALUE '4' after '3';

81ae3e5f9853b46c34a7287f51f3d2ea7cfd237e
alter table mock_tests add column date_closed boolean default false;
alter table mock_tests add column opening_date date;


ALTER TYPE target_exams_enum ADD VALUE '6' AFTER '5'
ALTER TYPE ontology_node_classes_enum ADD VALUE '3' AFTER '2';
