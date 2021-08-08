/*
 * Copyright (C) 2019-2021, TomTom (http://tomtom.com).
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.asciidoxy;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

/**
 * Class for testing nullability annotations.
 */
public class Nullability {

    public class DataClass {}

    public @Nullable DataClass getData() {}

    public @NonNull DataClass getDataNonNull() {}

    public void setData(@Nullable DataClass data) {}

    public void setDataNonNull(@NonNull DataClass data) {}
}
