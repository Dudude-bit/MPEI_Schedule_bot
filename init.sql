CREATE TABLE schedule (
  id serial unique,
  WeekDay VARCHAR(250) NOT NULL,
  num_object smallint NOT NULL,
  object varchar(250) NOT NULL,
  groupoid int NOT NULL,
  auditory varchar(250) NOT NULL,
  teacher varchar(250) NOT NULL,
  object_type varchar(250) NOT NULL,
  slug varchar(8) NOT NULL,
  week smallint NOT NULL,
  PRIMARY KEY (id)
);