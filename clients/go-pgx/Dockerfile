FROM golang:1.26 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY main.go ./
RUN CGO_ENABLED=0 go build -trimpath -o /workload .

FROM alpine:3.22
COPY --from=build /workload /workload
ENTRYPOINT ["/workload"]
