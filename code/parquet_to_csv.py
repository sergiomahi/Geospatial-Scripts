import pandas as pd
path = '/home/ec2-user/data/'
output_path = '/home/ec2-user/data/optus_sidney_part_20/'
for i in range(0, 10):
    print(i)
    input_filename = 'part-0000'+str(i)+'-12f2cad7-0df8-4ea4-b93c-99a65058a060-c000.snappy.parquet'
    df = pd.read_parquet(path+input_filename)
    df.to_csv(output_path+str(i=+'.csv')
