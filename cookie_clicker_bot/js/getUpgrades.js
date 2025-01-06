return Object.keys(Game.UpgradesById)
    .filter(key => Game.UpgradesById[key].bought === 0 && Game.UpgradesById[key].unlocked === 1)
    .reduce((acc, key) => {
        let obj = Game.UpgradesById[key];
        let returnObject = {
            "name": obj.name,
            "price": obj.getPrice(),
            "desc": obj.desc
        };
        if (obj.buildingTie != 0) {
            returnObject["building"] = Game.UpgradesById[key].buildingTie.name;
        }
        acc[key] = returnObject;
        return acc;
    }, {});
