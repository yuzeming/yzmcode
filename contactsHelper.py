import csv
import pdb
pdb.set_trace()
fin=csv.reader(open("contacts.csv"))
for name,phone,email in fin:

    fname=unicode(name,"utf-8")
    fout=open(fname+".vcf","w")
    name= "%r" %(name,)
    name=name.replace("\\x", "=").replace("'","").upper()
    name="N;ENCODING=QUOTED-PRINTABLE;CHARSET=utf-8:"+name
    vcard = "BEGIN:VCARD\nVERSION:3.0\n"
    vcard += name + "\n"
    if phone != "":
        vcard += "TEL:%s\n" % (phone,)
    if email !="":
        vcard += "EMAIL:%s\n" % (email,)
    vcard +="END:VCARD\n"
    fout.write(vcard)

    fout.close()

