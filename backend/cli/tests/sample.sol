pragma solidity ^0.8.0;

contract TestContract {
    uint256 public count = 0;

    function increment() public {
        count += 1;
    }
}
