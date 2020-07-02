# Copyright (C) 2019-2020, TomTom (http://tomtom.com).
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
"""Transcoding of API reference information from one language to another."""

from typing import Mapping, Tuple

from ..model import Compound, Member, ReferableElement
from .base import TranscoderBase, TranscoderError
from .kotlin import KotlinTranscoder

_transcoders: Mapping[Tuple[str, str], TranscoderBase] = {
    (KotlinTranscoder.SOURCE, KotlinTranscoder.TARGET): KotlinTranscoder(),
}


def transcode(element: ReferableElement, target: str) -> ReferableElement:
    """Transcode an element from its source language to another language.

    Args:
        element: Element to transcode.
        target:  Target language to transcode to.

    Returns:
        Version of `element` for language `target`.

    Raises:
        TranscoderError: Transcoding failed or is not supported.
    """
    transcoder = _transcoders.get((element.language, target), None)
    if transcoder is None:
        raise TranscoderError(f"Transcoding from {element.language} to {target} is not supported.")

    if isinstance(element, Compound):
        return transcoder.compound(element)
    elif isinstance(element, Member):
        return transcoder.member(element)
    else:
        assert False, "Invalid element to transcode."
        return element


__all__ = ["transcode"]
