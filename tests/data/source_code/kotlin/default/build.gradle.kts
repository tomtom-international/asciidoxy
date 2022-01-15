/*
 * Copyright (C) 2019, TomTom (http://tomtom.com).
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
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
    kotlin("jvm") version "1.5.31"
    id("org.jetbrains.dokka") version "1.5.31"
}

repositories {
    mavenCentral()
    mavenLocal()
}

val dokkaOutputDir = "$buildDir/dokka"

tasks {
    withType<KotlinCompile> {
        kotlinOptions.jvmTarget = "1.8"
    }
    dokkaHtml {
        outputDirectory.set(file(dokkaOutputDir))
    }
}

dependencies {
    dokkaHtmlPlugin("org.asciidoxy.dokka:asciidoxy-dokka:0.1-SNAPSHOT")
}
