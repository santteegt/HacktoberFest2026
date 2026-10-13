-- Create a hypertable for the sensor data
-- The default partitioning column is automatically 
-- the first column with a timestamp data type
-- (as a best practice, always use the timestamptz data type)
CREATE TABLE sensor_data (
  time TIMESTAMPTZ NOT NULL,
  sensor_id INTEGER,
  temperature DOUBLE PRECISION,
  cpu DOUBLE PRECISION,
  FOREIGN KEY (sensor_id) REFERENCES sensors (id)
) WITH (
  tsdb.hypertable
);