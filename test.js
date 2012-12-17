
describe("This is a test of", function() {
    it("failing tests", function() {
        var a = 1 + 1;
        throw "Ha ha!";
    });

    it("succeeding tests", function() {
        var a = 3 + 4;
        console.log(a);
    });
});
