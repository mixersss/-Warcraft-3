// Only explanatory strings changed by the 0.16.2 troop-effect increase.
// verify-0162 independently checks the new descriptions and all emitted effect data.
module.exports=s=>s.replace('Атака армии +4','Атака армии +3')
 .replace('Броня армии +1,5','Броня армии +1')
 .replace('Здоровье армии +10%','Здоровье армии +6,67%')
 .replace('Attack research adds 4 damage and armor adds 1.5 per rank. HP research adds 10% of base HP per rank.','Attack research adds 3 damage and armor adds 1 per rank. HP research adds 6.67% of base HP per rank.');
