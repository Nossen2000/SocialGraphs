/* ===========================================================================
   data.js — the ONLY file you edit.
   Regenerate it from your notebook with export_board_data.py, or hand-edit it.
   index.html reads these five globals and computes every number on the page
   from them. Nothing is hard-coded in the HTML, so the prose cannot disagree
   with the data.
   =========================================================================== */

const CASE = {
  /* "DRAFT" shows the yellow banner. Flip to "FINAL" only once
     AUDIT, FINDINGS and LIMITATION below are filled in. */
  status:     "DRAFT",

  group:      "Group ##",
  corpusNote: "303 Marvel character pages, English Wikipedia",

  /* The board gets unreadable past ~45 nodes. This draws only the N
     highest-degree characters. IMPORTANT: it affects the picture only —
     every statistic on the page is still computed from ALL edges. */
  boardTopN:  40,

  /* Week-4 communities: id -> display name. Rename them to something
     human once you've looked at who is in each. */
  communities: {
    1: "Community 1",
    2: "Community 2",
    3: "Community 3",
    4: "Community 4"
  }
};

/* ---------------------------------------------------------------------------
   NODES — one row per character.
   id   : must match the names used in EDGES exactly
   comm : week-4 community id (a key of CASE.communities)
   deg  : any size measure (in-degree works); controls dot size + top-N
   --------------------------------------------------------------------------- */
const NODES = [
  {id:"Iron Man",          comm:1, deg:9}, {id:"Captain America", comm:1, deg:9},
  {id:"Thor",              comm:1, deg:7}, {id:"Hulk",            comm:1, deg:7},
  {id:"Black Widow",       comm:1, deg:5}, {id:"Hawkeye",         comm:1, deg:4},
  {id:"Professor X",       comm:2, deg:8}, {id:"Magneto",         comm:2, deg:8},
  {id:"Wolverine",         comm:2, deg:9}, {id:"Storm",           comm:2, deg:6},
  {id:"Cyclops",           comm:2, deg:6}, {id:"Jean Grey",       comm:2, deg:6},
  {id:"Spider-Man",        comm:3, deg:10},{id:"Green Goblin",    comm:3, deg:6},
  {id:"Doctor Octopus",    comm:3, deg:5}, {id:"Mary Jane Watson",comm:3, deg:4},
  {id:"Venom",             comm:3, deg:5},
  {id:"Mister Fantastic",  comm:4, deg:7}, {id:"Invisible Woman", comm:4, deg:6},
  {id:"Thing",             comm:4, deg:5}, {id:"Human Torch",     comm:4, deg:5},
  {id:"Doctor Doom",       comm:4, deg:8}, {id:"Galactus",        comm:4, deg:4}
];

/* ---------------------------------------------------------------------------
   EDGES — one row per labelled link.
   s, t     : source and target character (must exist in NODES)
   rel      : "foe" | "ally" | "family" | "unlabeled"
   hit      : the keyword your word list matched, or null
   sentence : the REAL sentence from s's page that mentions t.
              Leave "" and the page renders an empty evidence slot.
              Never invent one — the empty slot is the honest state.
   --------------------------------------------------------------------------- */
const EDGES = [
  {s:"Iron Man",         t:"Captain America", rel:"foe",    hit:"fought",   sentence:""},
  {s:"Iron Man",         t:"Thor",            rel:"ally",   hit:"teammate", sentence:""},
  {s:"Captain America",  t:"Black Widow",     rel:"ally",   hit:"ally",     sentence:""},
  {s:"Thor",             t:"Hulk",            rel:"foe",    hit:"fought",   sentence:""},
  {s:"Hawkeye",          t:"Black Widow",     rel:"ally",   hit:"partner",  sentence:""},
  {s:"Hulk",             t:"Iron Man",        rel:"foe",    hit:"defeated", sentence:""},
  {s:"Captain America",  t:"Hawkeye",         rel:"ally",   hit:"joined",   sentence:""},

  {s:"Professor X",      t:"Magneto",         rel:"foe",    hit:"nemesis",  sentence:""},
  {s:"Professor X",      t:"Cyclops",         rel:"ally",   hit:"mentor",   sentence:""},
  {s:"Wolverine",        t:"Jean Grey",       rel:"ally",   hit:"teammate", sentence:""},
  {s:"Cyclops",          t:"Jean Grey",       rel:"family", hit:"married",  sentence:""},
  {s:"Magneto",          t:"Storm",           rel:"foe",    hit:"villain",  sentence:""},
  {s:"Storm",            t:"Wolverine",       rel:"ally",   hit:"teammate", sentence:""},
  {s:"Magneto",          t:"Wolverine",       rel:"foe",    hit:"fought",   sentence:""},

  {s:"Spider-Man",       t:"Green Goblin",    rel:"foe",    hit:"enemy",    sentence:""},
  {s:"Spider-Man",       t:"Doctor Octopus",  rel:"foe",    hit:"nemesis",  sentence:""},
  {s:"Spider-Man",       t:"Mary Jane Watson",rel:"family", hit:"married",  sentence:""},
  {s:"Spider-Man",       t:"Venom",           rel:"foe",    hit:"villain",  sentence:""},
  {s:"Venom",            t:"Green Goblin",    rel:"ally",   hit:"joined",   sentence:""},
  {s:"Green Goblin",     t:"Mary Jane Watson",rel:"foe",    hit:"killed",   sentence:""},

  {s:"Mister Fantastic", t:"Invisible Woman", rel:"family", hit:"married",  sentence:""},
  {s:"Invisible Woman",  t:"Human Torch",     rel:"family", hit:"brother",  sentence:""},
  {s:"Mister Fantastic", t:"Doctor Doom",     rel:"foe",    hit:"nemesis",  sentence:""},
  {s:"Thing",            t:"Human Torch",     rel:"ally",   hit:"teammate", sentence:""},
  {s:"Doctor Doom",      t:"Thing",           rel:"foe",    hit:"fought",   sentence:""},
  {s:"Galactus",         t:"Mister Fantastic",rel:"foe",    hit:"defeated", sentence:""},
  {s:"Thing",            t:"Invisible Woman", rel:"ally",   hit:"teammate", sentence:""},

  {s:"Spider-Man",       t:"Iron Man",        rel:"ally",   hit:"mentor",   sentence:""},
  {s:"Wolverine",        t:"Hulk",            rel:"foe",    hit:"fought",   sentence:""},
  {s:"Doctor Doom",      t:"Iron Man",        rel:"foe",    hit:"rival",    sentence:""},
  {s:"Magneto",          t:"Captain America", rel:"foe",    hit:"fought",   sentence:""},
  {s:"Human Torch",      t:"Spider-Man",      rel:"ally",   hit:"friend",   sentence:""},
  {s:"Thor",             t:"Galactus",        rel:"foe",    hit:"fought",   sentence:""},
  {s:"Storm",            t:"Black Widow",     rel:"ally",   hit:"joined",   sentence:""}
];

/* ---------------------------------------------------------------------------
   AUDIT — the hand-check. THIS IS THE ONE THAT UNLOCKS THE VERDICT.
   Draw ~40 labelled edges at random, open each sentence, decide if the
   label was right, and record it here.
   ok  : true = label correct | false = misfire
   why : what the sentence actually says (shown in the table, and in
         "False leads" when ok is false)
   --------------------------------------------------------------------------- */
const AUDIT = [
  // {s:"Spider-Man", t:"Green Goblin", rel:"foe", hit:"enemy", ok:true,
  //  why:"States the relationship directly in the same clause."},
  // {s:"Thor", t:"Hulk", rel:"foe", hit:"fought", ok:false,
  //  why:"They fought side by side against a third party. Keyword present, relationship inverted."},
];

/* ---------------------------------------------------------------------------
   FINDINGS — your written conclusions, one per claim.
   status: "ok"   supported, and `evidence` says what you checked
           "wait" measured but not verified
           "no"   the data did not support it  ← keep these, they earn marks
   --------------------------------------------------------------------------- */
const FINDINGS = [
  // {claim:"Foe edges cross community boundaries more often than ally edges.",
  //  status:"ok",
  //  evidence:"Foe 41% within vs ally 68% within, both outside the 95% shuffle band; "
  //         + "82% label precision on a 40-edge hand-check."},
];

/* One paragraph, in your own words. What would break this result? */
const LIMITATION = "";
