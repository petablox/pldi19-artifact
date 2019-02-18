// keep-derivable

// Given a set of constraints and a set of EDB tuples, filters those constraints which only produce those tuples which
// are derivable. Needed because mb.py may make some tuples unreachable.

#include <boost/algorithm/string/predicate.hpp>
using boost::starts_with;

#include <algorithm>
#include <cassert>
#include <chrono>
#include <ctime>
#include <iostream>
#include <iterator>
#include <limits>
#include <map>
#include <set>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include <fstream>
using namespace std;

#include "util.h"

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// 0. Prelude

string lit2Tuple(const string& literal) {
    if (starts_with(literal, "NOT ")) { return literal.substr(4); }
    else { return literal; }
}

vector<string> clause2Antecedents(const vector<string>& clause) {
    if (clause.size() > 1) {
        vector<string> ans(&clause[0], &clause[clause.size() - 1]);
        assert(clause.size() == ans.size() + 1);
        transform(ans.begin(), ans.end(), ans.begin(), &lit2Tuple);
        return ans;
    } else { return vector<string>(); }
}

string clause2Consequent(const vector<string>& clause) {
    string ans = clause[clause.size() - 1];
    assert(!starts_with(ans, "NOT "));
    return ans;
}

size_t maxAntecedentDob(const vector<string>& clause, const unordered_map<string, size_t>& tupleDob) {
    size_t ans = 0;
    for (const auto& literal : clause2Antecedents(clause)) {
        ans = max(ans, tupleDob.at(lit2Tuple(literal)));
    }
    return ans;
}

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// 1. Compute tuple DOB

unordered_map<string, size_t> computeTupleDob(const set<vector<string>>& allClauses,
                                              const unordered_set<string>& allTuples,
                                              const unordered_set<string>& effectiveEDB) {
    unordered_map<string, size_t> tupleDob;
    for (const auto& t : allTuples) {
        tupleDob[t] = effectiveEDB.find(t) == effectiveEDB.end() ? numeric_limits<size_t>::max() : 0;
    }

    size_t numChanged = 1;
    while (numChanged > 0) {
        numChanged = 0;
        for (const auto& clause : allClauses) {
            auto consequent = clause2Consequent(clause);
            size_t newDob = maxAntecedentDob(clause, tupleDob);
            if (newDob < numeric_limits<size_t>::max()) { newDob++; }
            if (newDob < tupleDob[consequent]) {
                numChanged++;
                tupleDob[consequent] = newDob;
            }
        }
    }

    size_t maxDob = 0, unreachableTuples = 0;
    for (const auto& tupleDobPair : tupleDob) {
        if (tupleDobPair.second < numeric_limits<size_t>::max()) {
            maxDob = max(maxDob, tupleDobPair.second);
        } else {
            clog << __LOGSTR__ << "Discovered unreachable tuple " << tupleDobPair.first << "." << endl;
            unreachableTuples++;
        }
    }
    clog << __LOGSTR__ << "Last (not necessarily useful) tuple birted at epoch " << maxDob << "." << endl;

    return tupleDob;
}

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// 2. Main

int main(int argc, char *argv[]) {
    clog << __LOGSTR__ << "Hello!" << endl;
    if (argc < 5) {
        cerr << __LOGSTR__ << "Insufficient arguments!" << endl
                           << "./keep-derivable allEDB.txt SemAlarm.txt SemAllAlarm.txt.ukd SemAllAlarm.txt" << endl;
        return 1;
    }
    string edbTupleFileName = argv[1];
    string newAlarmsFileName = argv[2];
    string allAlarmsFileName = argv[3];
    string allDerivableAlarmsFileName = argv[4];

    ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    // M1. Load clauses

    set<vector<string>> allClauses;
    map<vector<string>, string> allRuleNames;

    string inputLine;
    while (getline(cin, inputLine)) {
        istringstream inputLineStream(inputLine);

        string ruleName;
        inputLineStream >> ruleName;
        ruleName.pop_back();

        vector<string> clause;

        string token;
        bool lastNot = false;
        while (inputLineStream >> token) {
            if (token == "NOT") {
                lastNot = true;
            } else {
                if (token[token.size() - 1] == ',') {
                    token.pop_back();
                }
                clause.push_back(lastNot ? "NOT " + token : token);
                lastNot = false;
            }
        }

        assert(clause.size() >= 1);
        allClauses.insert(clause);
        allRuleNames[clause] = ruleName;
    }
    clog << __LOGSTR__ << "Loaded " << allClauses.size() << " clauses." << endl;

    ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    // M2. Compute all tuples and consequents,

    unordered_set<string> allTuples;
    set<string> allConsequents;

    for (const auto& clause : allClauses) {
        for (const auto& literal : clause) {
            allTuples.insert(lit2Tuple(literal));
        }
        allConsequents.insert(clause2Consequent(clause));
    }

    clog << __LOGSTR__ << "Discovered " << allTuples.size() << " tuples." << endl;
    clog << __LOGSTR__ << "Discovered " << allConsequents.size() << " consequents." << endl;

    // and load all input tuples and new alarms.

    unordered_set<string> allInputTuples;
    ifstream edbTupleFile(edbTupleFileName);
    string tup;
    while (edbTupleFile >> tup) allInputTuples.insert(tup);
    clog << __LOGSTR__ << "Loaded " << allInputTuples.size() << " input tuples." << endl;

    unordered_set<string> allNewAlarms;
    ifstream newAlarmsFile(newAlarmsFileName);
    while (newAlarmsFile >> tup) allNewAlarms.insert(tup);
    clog << __LOGSTR__ << "Loaded " << allNewAlarms.size() << " new alarms." << endl;

    ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    // 3. Compute dates of birth of each tuple, and the set of forward clauses

    const auto tupleDob = computeTupleDob(allClauses, allTuples, allInputTuples);
    unordered_set<vector<string>, vector_hash<string>> fwdClauses;
    for (const auto& clause : allClauses) {
        if (maxAntecedentDob(clause, tupleDob) < tupleDob.at(clause2Consequent(clause))) {
            fwdClauses.insert(clause);
        }
    }
    clog << __LOGSTR__ << "Discovered " << fwdClauses.size() << " forward clauses." << endl;

    // 3a. Confirm that all new alarms are derivable
    // NOTE: Not all new alarms need be derivable when keep-derivable.cpp is called with only the effective EDB set,
    // rather than all EDB nodes. The assertion has therefore been turned off.
    for (const auto& t : allNewAlarms) {
        if (tupleDob.at(t) == numeric_limits<size_t>::max()) {
            clog << __LOGSTR__ << "Unable to derive new alarm " << t << "." << endl;
            // assert(false);
        }
    }

    ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    // 4. Output the set of active clauses

    for (const auto& clause : fwdClauses) {
        if (tupleDob.at(clause2Consequent(clause)) < numeric_limits<size_t>::max()) {
            cout << allRuleNames[clause] << ": " << clause << endl;
            clog << __LOGSTR__ << "Emitting clause " << clause << endl;
        }
    }

    // 4a. Output the set of reachable alarms
    ifstream allAlarmsFile(allAlarmsFileName);
    ofstream allDerivableAlarmsFile(allDerivableAlarmsFileName);
    while (allAlarmsFile >> tup) {
        if (tupleDob.at(tup) < numeric_limits<size_t>::max()) {
            allDerivableAlarmsFile << tup << endl;
        }
    }
    allDerivableAlarmsFile.close();

    clog << __LOGSTR__ << "Bye!" << endl;
    return 0;
}
