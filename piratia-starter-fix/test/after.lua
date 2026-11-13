
local names={"Argent City","Shaitan City","Icicle Castle","Аргент","Шайтан","Ледынь"}
for i,name in ipairs(names) do
 local r={birth=name}
 local born=triggers[88888]
 for _,a in ipairs(born.actions) do if a.f==MultiTrigger then a.f(r,nil,nil,table.unpack(a.args)) else a.f(r,table.unpack(a.args)) end end
 check(r.mission==((i-1)%3+1) and r.boxes==1)
 StarterBirthAliasesRecover01(r); check(r.boxes==1)
 local missing={birth=name}; StarterBirthAliasesRecover01(missing)
 check(missing.mission==((i-1)%3+1) and missing.boxes==1)
 StarterBirthAliasesRecover01(missing);check(missing.boxes==1)
end
for _,fields in ipairs({{record=1},{record=2},{record=3},{mission=1},{mission=3},{mission=59},{record=58},{job=1},{player=0},{free=0},{owned=436},{bank=985},{equip=988},{error=true},{birth="Unknown City"},{refused=true}}) do
 local r={birth="Аргент"};for k,v in pairs(fields) do r[k]=v end
 StarterBirthAliasesRecover01(r);check(r.boxes==nil)
end
return checks
