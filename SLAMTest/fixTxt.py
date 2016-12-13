with open("log_2.txt", "r") as f:
	a = f.readlines()
newlist = []
for e in a:
	if ("[laser]" in e):
		index = e.find("[l")
		newlist.append(e[index+len("[laser]"):])

with open("slamfixed2.txt", "w") as f2:
	for e in newlist:
		f2.write(e)


