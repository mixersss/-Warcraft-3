// Named silhouettes, not just a palette swap of one generic ring.
export const TECHNIQUES={
 naruto:['rasengan','clones','kyubi','rasenganGiant'],sasuke:['chidori','fireball','sharingan','kirin'],
 sakura:['earth','seal','healing','earthBloom'],lee:['leafKick','lotus','gates','lotusStorm'],
 neji:['kaiten','palms','byakugan','palms128'],hinata:['kaiten','palms','byakugan','lionFists'],
 tenten:['weapons','seal','weaponStorm','twinDragons'],shikamaru:['shadow','sealShot','strategy','shadowBind'],
 kiba:['fang','dog','beast','wolf'],gaara:['sandCoffin','sandShield','sandWave','sandBurial'],
 kankuro:['puppet','poison','puppetTrap','puppetDance'],temari:['wind','windBarrier','tornado','windSummon'],
 kakashi:['chidori','waterDragon','dog','lightningCuts'],itachi:['fireball','crows','redMoon','blackFlame'],
 jiraiya:['rasengan','fireball','frog','sage'],orochimaru:['snakeSword','snake','shedding','manda']
};
export const visualFor=(hero,index)=>TECHNIQUES[hero]?.[index]||'chakra';
