# Copyright (C) 2019, TomTom (http://tomtom.com).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Test test functionality for partial model comparison."""

from asciidoxy.model import Compound, Parameter

from .matchers import (
    AtLeast,
    HasNot,
    IsEmpty,
    IsFalse,
    IsNone,
    IsNotEmpty,
    IsTrue,
    PartialModel,
    SizeIs,
    Unordered,
    m_compound,
)


def test_match_only_specified_attributes():
    PartialModel(Compound, id="abc").assert_matches(Compound(id="abc"))
    PartialModel(Compound, id="abc").assert_matches(Compound(id="abc", name="name"))
    PartialModel(Compound, name="name").assert_matches(Compound(id="abc", name="name"))
    PartialModel(Compound, id="abc", name="name").assert_matches(Compound(id="abc", name="name"))

    PartialModel(Compound, id="abdc").assert_not_matches(Compound(id="abc"))
    PartialModel(Compound, id="abdc").assert_not_matches(Compound(id="abc", name="name"))
    PartialModel(Compound, name="dname").assert_not_matches(Compound(id="abc", name="name"))
    PartialModel(Compound, id="abdc",
                 name="dname").assert_not_matches(Compound(id="abc", name="name"))


def test_match_nested_expectations():
    PartialModel(Compound, members=[PartialModel(Compound, id="abc")
                                    ]).assert_matches(Compound(members=[Compound(id="abc")]))
    PartialModel(Compound,
                 members=[PartialModel(Compound, members=[PartialModel(Compound, id="abc")])
                          ]).assert_matches(
                              Compound(members=[Compound(members=[Compound(id="abc")])]))

    PartialModel(Compound, members=[PartialModel(Compound, id="abcd")
                                    ]).assert_not_matches(Compound(members=[Compound(id="abc")]))
    PartialModel(Compound,
                 members=[PartialModel(Compound,
                                       id="abcd")]).assert_not_matches(Compound(members=[]))
    PartialModel(Compound,
                 members=[PartialModel(Compound, members=[PartialModel(Compound, id="abcd")])
                          ]).assert_not_matches(
                              Compound(members=[Compound(members=[Compound(id="abc")])]))


def test_match_nested_original_objects():
    PartialModel(Compound, members=[Compound(id="abc")
                                    ]).assert_matches(Compound(members=[Compound(id="abc")]))
    PartialModel(Compound,
                 members=[PartialModel(Compound, members=[Compound(id="abc")])]).assert_matches(
                     Compound(members=[Compound(members=[Compound(id="abc")])]))

    PartialModel(Compound, members=[Compound(id="dabc")
                                    ]).assert_not_matches(Compound(members=[Compound(id="abc")]))
    PartialModel(Compound, members=[PartialModel(Compound, members=[Compound(id="dabc")])
                                    ]).assert_not_matches(
                                        Compound(members=[Compound(members=[Compound(id="abc")])]))


def test_type_must_match():
    PartialModel(Compound, id="abc").assert_matches(Compound(id="abc"))
    PartialModel(Compound, name="abc").assert_not_matches(Parameter(name="abc"))


def test_unordered():
    m_compound(members=Unordered(m_compound(name="a"), m_compound(name="b"))).assert_matches(
        Compound(members=[Compound(name="a"), Compound(name="b")]))
    m_compound(members=Unordered(m_compound(name="b"), m_compound(name="a"))).assert_matches(
        Compound(members=[Compound(name="a"), Compound(name="b")]))
    m_compound(members=Unordered(m_compound(name="a"), m_compound(name="b"))).assert_matches(
        Compound(members=[Compound(name="b"), Compound(name="a")]))

    m_compound(members=Unordered(m_compound(name="a"), m_compound(name="b"))).assert_not_matches(
        Compound(members=[Compound(name="c"), Compound(name="b")]))
    m_compound(members=Unordered(m_compound(name="a"), m_compound(name="b"))).assert_not_matches(
        Compound(members=[Compound(name="a")]))


def test_atleast():
    m_compound(members=AtLeast(m_compound(name="a"), m_compound(name="b"))).assert_matches(
        Compound(members=[Compound(name="a"), Compound(name="b")]))
    m_compound(members=AtLeast(m_compound(name="a"))).assert_matches(
        Compound(members=[Compound(name="a"), Compound(name="b")]))
    m_compound(members=AtLeast(m_compound(name="b"))).assert_matches(
        Compound(members=[Compound(name="a"), Compound(name="b")]))

    m_compound(members=AtLeast(m_compound(name="a"), m_compound(name="c"))).assert_not_matches(
        Compound(members=[Compound(name="a"), Compound(name="b")]))
    m_compound(members=AtLeast(m_compound(name="a"), m_compound(name="b"))).assert_not_matches(
        Compound(members=[Compound(name="a"), Compound(name="c")]))
    m_compound(members=AtLeast(m_compound(name="a"), m_compound(name="b"))).assert_not_matches(
        Compound(members=[Compound(name="a")]))


def test_hasnot():
    m_compound(members=HasNot(m_compound(name="a"))).assert_matches(
        Compound(members=[Compound(name="c"), Compound(name="d")]))
    m_compound(members=HasNot(m_compound(name="a"), m_compound(name="b"))).assert_matches(
        Compound(members=[Compound(name="c"), Compound(name="d")]))

    m_compound(members=HasNot(m_compound(name="a"), m_compound(name="b"))).assert_not_matches(
        Compound(members=[Compound(name="a"), Compound(name="d")]))
    m_compound(members=HasNot(m_compound(name="a"), m_compound(name="b"))).assert_not_matches(
        Compound(members=[Compound(name="c"), Compound(name="b")]))
    m_compound(members=HasNot(m_compound(name="a"), m_compound(name="b"))).assert_not_matches(
        Compound(members=[Compound(name="a"), Compound(name="b")]))


def test_isempty():
    m_compound(name=IsEmpty()).assert_matches(Compound(name=None))
    m_compound(name=IsEmpty()).assert_matches(Compound(name=""))
    m_compound(name=IsEmpty()).assert_not_matches(Compound(name="bla"))


def test_isnotempty():
    m_compound(name=IsNotEmpty()).assert_matches(Compound(name="bla"))
    m_compound(name=IsNotEmpty()).assert_matches(Compound(name=" "))
    m_compound(name=IsNotEmpty()).assert_matches(Compound(name="   "))
    m_compound(name=IsNotEmpty()).assert_matches(Compound(name="\t"))

    m_compound(name=IsNotEmpty()).assert_not_matches(Compound(name=""))
    m_compound(name=IsNotEmpty()).assert_not_matches(Compound(name=None))


def test_isfalse():
    m_compound(static=IsFalse()).assert_matches(Compound(static=False))

    m_compound(static=IsFalse()).assert_not_matches(Compound(static=True))
    m_compound(static=IsFalse()).assert_not_matches(Compound(static="bla"))
    m_compound(static=IsFalse()).assert_not_matches(Compound(static=None))


def test_istrue():
    m_compound(static=IsTrue()).assert_matches(Compound(static=True))

    m_compound(static=IsTrue()).assert_not_matches(Compound(static=False))
    m_compound(static=IsTrue()).assert_not_matches(Compound(static="bla"))
    m_compound(static=IsTrue()).assert_not_matches(Compound(static=None))


def test_isnone():
    m_compound(name=IsNone()).assert_matches(Compound(name=None))

    m_compound(name=IsNone()).assert_not_matches(Compound(name=""))
    m_compound(name=IsNone()).assert_not_matches(Compound(name="bla"))
    m_compound(name=IsNone()).assert_not_matches(Compound(name=0))


def test_sizeis():
    m_compound(members=SizeIs(1)).assert_matches(Compound(members=[Compound()]))
    m_compound(members=SizeIs(2)).assert_matches(Compound(members=[Compound(), Compound()]))
    m_compound(members=SizeIs(0)).assert_matches(Compound(members=[]))

    m_compound(members=SizeIs(1)).assert_not_matches(Compound(members=[Compound(), Compound()]))
    m_compound(members=SizeIs(2)).assert_not_matches(Compound(members=[Compound()]))
    m_compound(members=SizeIs(0)).assert_not_matches(Compound(members=[Compound()]))

    # Constructor replaces None with empty list
    compound_members_none = Compound()
    compound_members_none.members = None
    m_compound(members=SizeIs(0)).assert_not_matches(compound_members_none)
