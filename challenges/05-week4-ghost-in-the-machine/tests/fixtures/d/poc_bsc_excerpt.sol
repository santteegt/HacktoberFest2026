contract ContractTest is Test {
    address victim = 0x1111111111111111111111111111111111111111;
    function setUp() public { vm.createSelectFork("bsc", 1234); }
}
