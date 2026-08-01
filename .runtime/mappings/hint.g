<! STRUCT CONVERSION AHEAD OF *>
explain marcos conv;
explain marcos down(type{letters});
explain constant dyn;

n <= conv(test-1 test-1 test-1 test-1 test-1 test-1 test-1 test-1 test-1 test-1 test-1 test-1 test-1 test-1 test-1 test-1);

module ptr (
    struct any -> bytes; 
    encoding "ASCII/UTF-8";
    variable x, y
) {
    down down down down down down down down (x);
    foreach u in x {
        case u and y
        case u and not y
        case not u and y
        case not u and not y
    => (0, 1, 1, 0)
    }
}
    
ptr0 = ptr(r"M_\YSKNDAC_SPMOX", n);
ptr1 = ptr(r"")

<! SWITCH DSL FAMILY alike ". . . :">
<! IGNORE: BLANK LINE, BLANK SEPERATOR>
LOC (. . / conv(ptr0) / dyn) {
    DEFINE (A [B, *]);
    CHECK 00 [25, 26, 31, 34, 35];
    CHECK 11 [19] 01 [8] 04 [30] 05 [24, 74];
}


