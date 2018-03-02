from dataset_processing import *

data = read_stored_data("hotttnesss.txt")

only_valid = []
for l in data:
    if l[3] == l[3]:
        only_valid += [[str(l[0]), str(l[1]), str(l[2]), float(l[3])]]

only_valid.sort(key=lambda x: x[3], reverse=True)

fw = open("tracks_with_hotttnesss.txt", 'wb')

for l in only_valid:
    fw.write(l[0] + "\t" + l[1] + "\t" + l[2] + "\t" + str(l[3]) + "\n")

fw.close()
