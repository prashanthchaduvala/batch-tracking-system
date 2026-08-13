import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API_URL = "http://127.0.0.1:8000/api";

function App() {
  const [token, setToken] = useState(
    localStorage.getItem("access_token")
  );

  const [username, setUsername] = useState("prashanth");
  const [password, setPassword] = useState("Test@123");

  const [batches, setBatches] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [page, setPage] = useState(1);
  const [nextPage, setNextPage] = useState(null);
  const [previousPage, setPreviousPage] = useState(null);

  async function login(event) {
    event.preventDefault();
    setError("");

    try {
      const response = await axios.post(
        `${API_URL}/token/`,
        {
          username,
          password,
        }
      );

      localStorage.setItem(
        "access_token",
        response.data.access
      );

      localStorage.setItem(
        "refresh_token",
        response.data.refresh
      );

      setToken(response.data.access);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Invalid username or password"
      );
    }
  }

  function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setToken(null);
    setBatches([]);
  }

  async function fetchBatches() {
    if (!token) return;

    setLoading(true);
    setError("");

    try {
      const params = {
        page,
      };

      if (statusFilter) {
        params.status = statusFilter;
      }

      if (typeFilter) {
        params.type = typeFilter;
      }

      const response = await axios.get(
        `${API_URL}/batches/`,
        {
          params,
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setBatches(response.data.results || []);
      setNextPage(response.data.next);
      setPreviousPage(response.data.previous);
    } catch (err) {
      if (err.response?.status === 401) {
        logout();
        setError("Session expired. Please login again.");
      } else {
        setError(
          err.response?.data?.detail ||
            "Failed to load batches"
        );
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchBatches();
  }, [token, page, statusFilter, typeFilter]);

  async function updateStatus(batchId, newStatus) {
    const oldBatches = [...batches];

    // Optimistic UI update
    setBatches((current) =>
      current.map((batch) =>
        batch.id === batchId
          ? { ...batch, status: newStatus }
          : batch
      )
    );

    try {
      const response = await axios.patch(
        `${API_URL}/batches/${batchId}/status/`,
        {
          status: newStatus,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setBatches((current) =>
        current.map((batch) =>
          batch.id === batchId
            ? response.data
            : batch
        )
      );
    } catch (err) {
      // Roll back optimistic change
      setBatches(oldBatches);

      setError(
        err.response?.data?.error ||
          "Failed to update batch status"
      );
    }
  }

  if (!token) {
    return (
      <div className="login-page">
        <form
          className="login-card"
          onSubmit={login}
        >
          <h1>Batch Tracking System</h1>

          <p>Login to continue</p>

          {error && (
            <div className="error">
              {error}
            </div>
          )}

          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) =>
              setUsername(e.target.value)
            }
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) =>
              setPassword(e.target.value)
            }
          />

          <button type="submit">
            Login
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="app">
      <header>
        <div>
          <h1>Batch Tracking System</h1>
          <p>Diagnostic batch management</p>
        </div>

        <button onClick={logout}>
          Logout
        </button>
      </header>

      <main>
        <section className="filters">
          <div>
            <label>Status</label>

            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">
                All
              </option>

              <option value="queued">
                Queued
              </option>

              <option value="processing">
                Processing
              </option>

              <option value="completed">
                Completed
              </option>

              <option value="failed">
                Failed
              </option>
            </select>
          </div>

          <div>
            <label>Batch Type</label>

            <input
              type="text"
              placeholder="Blood Panel"
              value={typeFilter}
              onChange={(e) => {
                setTypeFilter(e.target.value);
                setPage(1);
              }}
            />
          </div>

          <button onClick={fetchBatches}>
            Refresh
          </button>
        </section>

        {error && (
          <div className="error">
            {error}
          </div>
        )}

        {loading ? (
          <div className="message">
            Loading batches...
          </div>
        ) : batches.length === 0 ? (
          <div className="message">
            No batches found.
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Sample ID</th>
                <th>Batch Type</th>
                <th>Submitted By</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {batches.map((batch) => (
                <tr key={batch.id}>
                  <td>{batch.id}</td>

                  <td>
                    {batch.sample_id}
                  </td>

                  <td>
                    {batch.batch_type}
                  </td>

                  <td>
                    {batch.submitted_by}
                  </td>

                  <td>
                    <span
                      className={`status ${batch.status}`}
                    >
                      {batch.status}
                    </span>
                  </td>

                  <td>
                    {batch.status === "queued" && (
                      <button
                        onClick={() =>
                          updateStatus(
                            batch.id,
                            "processing"
                          )
                        }
                      >
                        Start
                      </button>
                    )}

                    {batch.status ===
                      "processing" && (
                      <>
                        <button
                          onClick={() =>
                            updateStatus(
                              batch.id,
                              "completed"
                            )
                          }
                        >
                          Complete
                        </button>

                        <button
                          onClick={() =>
                            updateStatus(
                              batch.id,
                              "failed"
                            )
                          }
                        >
                          Fail
                        </button>
                      </>
                    )}

                    {batch.status === "failed" && (
                      <button
                        onClick={() =>
                          updateStatus(
                            batch.id,
                            "processing"
                          )
                        }
                      >
                        Retry
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <div className="pagination">
          <button
            disabled={!previousPage}
            onClick={() =>
              setPage((p) => p - 1)
            }
          >
            Previous
          </button>

          <span>Page {page}</span>

          <button
            disabled={!nextPage}
            onClick={() =>
              setPage((p) => p + 1)
            }
          >
            Next
          </button>
        </div>
      </main>
    </div>
  );
}

export default App;