
var assert = require('assert');

describe("This is a test of", function() {
    it("failing tests", function() {
        var a = 1 + 1;
        console.log("Showing that output is grouped with right test");
        throw "Ha ha!";
    });

    it("succeeding tests", function() {
        var a = 3 + 4;
        console.log(a);
    });

    it("Fails again", function() {
        var a = 5;
        console.log("Again, output should be grouped correctly: " + a);
        throw "Ho ho ho";
    });

    it("Succeeds again", function() {
        var a = 88 + 7;
        assert.equal(a, 95);
    });
});
