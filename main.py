import time

start = time.time()
import pathway as pw
end = time.time()
print(f"Took {end - start} to load pathway :)")

class InputSchema(pw.Schema):
    name: str
    value: int
    timestamp: str

input_table = pw.io.csv.read(
    './data/',
    schema=InputSchema,
    mode="streaming"
)

result = input_table.reduce(
    total=pw.reducers.sum(input_table.value),
    count=pw.reducers.count()
)

pw.io.csv.write(result, "output.csv")

pw.run()
