function getYearRanges(startYear, span) {
    var currentYear = new Date().getFullYear();
    var ranges = [];

    for (var y = startYear; y <= currentYear; y += span) {
        var from = y;
        var to = Math.min(y + span - 1, currentYear);
        ranges.push({ from: from, to: to });
    }

    return ranges;
}

function getPrefixFromYear(year) {
    return String(Math.max(0, year - 2003)).padStart(2, "0");
}
