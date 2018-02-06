(defproject frost-fighters "0.1.0-SNAPSHOT"
  :description "FIXME: write description"
  :url "http://example.com/FIXME"
  :license {:name "Eclipse Public License"
            :url "http://www.eclipse.org/legal/epl-v10.html"}
  :dependencies [[org.clojure/clojure "1.9.0"]
                 [org.clojure/core.async "0.4.474"]
                 [org.clojure/core.match "0.3.0-alpha5"]
                 [ring/ring "1.6.3"]
                 [compojure "1.6.0"]
                 [http-kit "2.2.0"]]
  :main ^:skip-aot frost-fighters.core
  :target-path "target/%s"
  :profiles {:uberjar {:aot :all}})