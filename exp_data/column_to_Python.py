# paste data into https://delim.co/#
# copy output data to 'data

data = "-0.2	0	0,-0.15	0	0,-0.1	0	0,-0.05	0	0,0	0	0,0.05	0	0,0.1	0	0,0.15	0.66	0.72,0.2	4.88	0.98,0.25	9.06	1.1,0.3	11.35	0.98,0.35	13.16	0.96,0.4	13.18	1.06,0.45	12.03	0.96,0.5	12.03	1.02,0.55	8.55	1.7,0.6	7.7	1.76"

b = data.split(",")
print(len(b))

for idx, item in enumerate(b):
  b[idx] = item.split("\t")

output = []
for idx, item in enumerate(b):
  print(item[0])
  output.append({
    "i_inj": item[0],
    "mean": item[1],
    "std": item[2]
  })

import json
json.dumps(output)