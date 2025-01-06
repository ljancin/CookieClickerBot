return Object.keys(Game.Objects)
    .reduce((acc, key) => {
        let obj = Game.Objects[key];
        acc[key] = {
            "baseCps": obj.baseCps
        };
        return acc;
    }, {});
