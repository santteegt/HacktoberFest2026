// Submitted by EthereumHistory (ethereumhistory.com)
pragma solidity ^0.4.11;

contract Token {
    function balanceOf(address _owner) public returns (uint256 balance);
    function transfer(address _to, uint256 _value) public returns (bool success);
}

contract UserWallet {
    address public owner;

    modifier onlyOwner {
        if (msg.sender != owner) throw;
        _;
    }

    function UserWallet() {
        owner = msg.sender;
    }

    function() payable {}

    function collectToken(address token) onlyOwner {
        Token t = Token(token);
        uint256 balance = t.balanceOf(this);
        t.transfer(owner, balance);
    }

    function destroy() onlyOwner {
        selfdestruct(owner);
    }

    function collect() onlyOwner {
        if (!owner.send(this.balance)) throw;
    }
}