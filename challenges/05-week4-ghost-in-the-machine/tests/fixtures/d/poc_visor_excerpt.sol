contract ContractTest is Test {
    IRewardsHypervisor irrewards = IRewardsHypervisor(0xC9f27A50f82571C1C8423A42970613b8dBDA14ef);
    IvVISR visr = IvVISR(0x3a84aD5d16aDBE566BAA6b3DafE39Db3D5E261E5);
    CheatCodes cheats = CheatCodes(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D);
    IWETH weth = IWETH(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);
    function setUp() public {
        cheats.createSelectFork("mainnet", 13_849_006); //fork mainnet at block 13849006
    }
}
